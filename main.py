from fastapi import FastAPI, Request, HTTPException, Depends, status, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import func
import pandas as pd
import re
import sqlparse

from db_init import Base, UserModel, TaskModel, SchemaTableModel, SchemaColumnModel, UserProgressModel, MockResultModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DB_URL = "oracle+cx_oracle://USER_APP:maksim2003@158.160.94.135:1521/XE"
TEST_DB_URL = "oracle+cx_oracle://USER_APP:maksim2003@158.160.94.135:1521/XE"  # Тестовая БД для проверки запросов

engine = create_engine(DB_URL)
test_engine = create_engine(TEST_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройки JWT
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_SECRET_KEY = "admin"

# Информация о требуемых столбцах для каждой задачи
TASK_COLUMNS_INFO = {
    1: "Результат должен содержать столбцы: id, name, department_id, salary, hire_date",
    2: "Результат должен содержать столбцы: department_id, department_name, count",
    3: "Результат должен содержать столбцы: employee_name, department_name, project_count",
    4: "Результат должен содержать столбцы: month, product, total_sales, running_total",
    5: "Результат должен содержать столбцы: employee_id, employee_name, department_id, manager_employee_id"
}

# Словарь разрешенных таблиц для каждой задачи
ALLOWED_TABLES = {
    1: ["employees"],
    2: ["employees", "departments"],
    3: ["employees", "departments", "projects", "employee_projects"],
    4: ["sales", "products", "customers"],
    5: ["employees", "departments"]
}


task_descriptions = {
    1: """
    Write a query to select all employees from the employees table.\n

    Expected columns in the result: id, name, department_id, salary, hire_date
    """,
    2: """
    Count the number of employees in each department.\n

    Expected columns in the result: department_id, department_name, count
    """,
    3: """
    Join multiple tables and filter the results based on conditions. \n
    Find the number of projects each employee in the Engineering department is involved in.\n

    Expected columns in the result: employee_name, department_name, project_count
    """,
    4: """
    Use window functions to calculate running totals.\n
    Calculate the monthly total sales and running total for the 'Laptop' product.\n

    Expected columns in the result: month, product, total_sales, running_total\n
    """,
    5: """
    Write a query to display the employee hierarchy.\n
    Show each employee along with their manager.\n

    Expected columns in the result: employee_id, employee_name, department_id, manager_employee_id\n
    """
}

def get_result_schema_for_task(task_id):
    result_schemas = {
        1: [
            {"name": "id", "type": "INTEGER", "description": "Employee ID"},
            {"name": "name", "type": "VARCHAR", "description": "Employee name"},
            {"name": "department_id", "type": "INTEGER", "description": "Department ID"},
            {"name": "salary", "type": "DECIMAL", "description": "Employee salary"},
            {"name": "hire_date", "type": "DATE", "description": "Date when employee was hired"}
        ],
        2: [
            {"name": "department_id", "type": "INTEGER", "description": "Department ID"},
            {"name": "department_name", "type": "VARCHAR", "description": "Department name"},
            {"name": "count", "type": "INTEGER", "description": "Number of employees in the department"}
        ],
        3: [
            {"name": "employee_name", "type": "VARCHAR", "description": "Employee name"},
            {"name": "department_name", "type": "VARCHAR", "description": "Department name"},
            {"name": "project_count", "type": "INTEGER", "description": "Number of projects the employee is working on"}
        ],
        4: [
            {"name": "month", "type": "VARCHAR/DATE", "description": "Month of sales"},
            {"name": "product", "type": "VARCHAR", "description": "Product name"},
            {"name": "total_sales", "type": "DECIMAL", "description": "Total sales amount for the month"},
            {"name": "running_total", "type": "DECIMAL", "description": "Running total of sales"}
        ],
        5: [
            {"name": "employee_name", "type": "VARCHAR", "description": "Employee name"},
            {"name": "level", "type": "INTEGER", "description": "Hierarchy level"},
            {"name": "manager_name", "type": "VARCHAR", "description": "Manager name (NULL for top level)"}
        ]
    }

    return result_schemas.get(task_id, [])

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    secret_key: Optional[str] = None

class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_admin: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskResponse(BaseModel):
    id: int
    name: str
    difficulty: str
    solved: bool = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def is_query_safe(query, task_id):
    """
    Проверяет, что запрос обращается только к разрешенным таблицам для данной задачи.

    Возвращает (is_safe, error_message):
        - is_safe: булево значение, True если запрос безопасен
        - error_message: сообщение об ошибке или None, если запрос безопасен
    """
    if task_id not in ALLOWED_TABLES:
        return False, f"Неизвестное задание: {task_id}"

    allowed = ALLOWED_TABLES[task_id]

    try:
        parsed = sqlparse.parse(query)
        if not parsed:
            return False, "Невозможно разобрать запрос"

        query_lower = query.lower()

        # Проверяем на наличие системных таблиц или пользовательских таблиц
        system_tables = ["users", "user_progress", "tasks", "mock_results",
                        "schema_tables", "schema_columns"]

        for table in system_tables:
            if re.search(r'\b' + table + r'\b', query_lower):
                return False, f"Запрос содержит обращение к запрещенной системной таблице: {table}"

        used_tables = []
        for table in get_all_possible_tables():
            if re.search(r'\b' + table + r'\b', query_lower):
                used_tables.append(table)

        # Проверяем, что все использованные таблицы разрешены для данной задачи
        disallowed_tables = [table for table in used_tables if table not in allowed]
        if disallowed_tables:
            return False, f"Запрос содержит обращение к таблицам, которые не относятся к данной задаче: {', '.join(disallowed_tables)}"

        # Дополнительно проверяем на наличие SQL-инъекций или опасных операций
        dangerous_operations = ["drop", "truncate", "delete", "update", "insert", "alter", "create",
                              "grant", "revoke", "commit", "rollback", "savepoint"]

        for op in dangerous_operations:
            if re.search(r'\b' + op + r'\b', query_lower):
                return False, f"Запрос содержит запрещенную операцию: {op}"

        return True, None
    except Exception as e:
        return False, f"Ошибка при проверке безопасности запроса: {str(e)}"

def get_all_possible_tables():
    """Возвращает список всех возможных таблиц в системе"""
    all_tables = set()
    for tables in ALLOWED_TABLES.values():
        all_tables.update(tables)

    all_tables.update(["users", "user_progress", "tasks", "mock_results",
                    "schema_tables", "schema_columns"])

    return all_tables


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_test_engine():
    return test_engine

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

def execute_query(query, engine):
    """Выполняет SQL запрос и возвращает результат в виде DataFrame"""
    try:
        with engine.connect() as connection:
            sql = text(query)
            result = connection.execute(sql)
            column_names = [str(col).lower() for col in result.keys()]

            rows = result.fetchall()

            # Создаем список словарей для безопасной сериализации в JSON
            data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    if value is None:
                        row_dict[column_names[i]] = None
                    else:
                        row_dict[column_names[i]] = str(value)
                data.append(row_dict)

            return data, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)


def compare_results(actual_results, expected_data):
    """Сравнивает полученный результат с эталонным и возвращает результат и информацию об ошибке"""
    if actual_results is None or expected_data is None:
        return False

    try:
        # Проверяем, что количество записей совпадает
        if len(actual_results) != len(expected_data):
            return False

        # Если результаты пустые, считаем совпадением
        if len(actual_results) == 0 and len(expected_data) == 0:
            return True

        # Проверяем, что наборы столбцов совпадают (игнорируя регистр)
        actual_keys = set(k.lower() for k in actual_results[0].keys())
        expected_keys = set(k.lower() for k in expected_data[0].keys())

        if actual_keys != expected_keys:
            return False

        # Создаем нормализованные копии для сравнения
        normalized_actual = []
        for row in actual_results:
            new_row = {}
            for key in row.keys():
                value = row[key]
                if value is not None and 'date' in key.lower() and isinstance(value, str) and ' ' in value:
                    value = value.split(' ')[0]
                new_row[key.lower()] = str(value) if value is not None else None
            normalized_actual.append(new_row)

        normalized_expected = []
        for row in expected_data:
            new_row = {}
            for key in row.keys():
                value = row[key]
                if value is not None and 'date' in key.lower() and isinstance(value, str) and len(value) > 10:
                    value = value[:10]
                new_row[key.lower()] = str(value) if value is not None else None
            normalized_expected.append(new_row)

        all_keys = sorted(expected_keys)

        def sort_key(row):
            return tuple(str(row.get(key, "")) for key in all_keys)

        sorted_actual = sorted(normalized_actual, key=sort_key)
        sorted_expected = sorted(normalized_expected, key=sort_key)

        # Проверка, что каждая строка совпадает
        for i, (actual_row, expected_row) in enumerate(zip(sorted_actual, sorted_expected)):
            if actual_row != expected_row:
                return False

        return True
    except Exception as e:
        # Логируем ошибку только на сервере
        print(f"Error comparing results: {e}")
        import traceback
        traceback.print_exc()
        return False




@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(UserModel).filter(UserModel.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        existing_email = db.query(UserModel).filter(UserModel.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

        if user.secret_key and user.secret_key != ADMIN_SECRET_KEY:
            raise HTTPException(status_code=400, detail="Wrong admin key")

        user_id = str(uuid.uuid4())
        new_user = UserModel(
            id=user_id,
            username=user.username,
            email=user.email,
            password=user.password,
            # add is_admin here
        )

        db.add(new_user)
        db.commit()

        tasks = db.query(TaskModel).all()

        try:
            max_id_result = db.query(func.max(UserProgressModel.id)).scalar()
            next_id = 1 if max_id_result is None else max_id_result + 1
        except Exception as e:
            print(f"Error getting max ID: {e}")
            next_id = 1

        for task in tasks:
            try:
                progress = UserProgressModel(
                    id=next_id,
                    user_id=user_id,
                    task_id=task.id,
                    solved=False
                )
                db.add(progress)
                next_id += 1
            except Exception as e:
                print(f"Error adding progress for task {task.id}: {e}")
                db.rollback()  # Отменяем изменения при ошибке
                raise HTTPException(status_code=500, detail=f"Error initializing task progress: {str(e)}")

        db.commit()

        return {"message": "User registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error during registration: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()

    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/tasks")
async def get_tasks(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(TaskModel).all()

    user_progress_records = db.query(UserProgressModel).filter(
        UserProgressModel.user_id == current_user.id
    ).all()

    progress_dict = {record.task_id: record.solved for record in user_progress_records}

    user_tasks = []
    for task in tasks:
        task_with_status = {
            "id": task.id,
            "name": task.name,
            "difficulty": task.difficulty,
            "solved": progress_dict.get(task.id, False)
        }
        user_tasks.append(task_with_status)

    return user_tasks

@app.get("/api/user/stats")
async def get_user_stats(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    solved_count = db.query(UserProgressModel).filter(
        UserProgressModel.user_id == current_user.id,
        UserProgressModel.solved == True
    ).count()

    total_count = db.query(TaskModel).count()

    if total_count > 0:
        completion_percentage = (solved_count / total_count) * 100
    else:
        completion_percentage = 0

    return {
        "solved_count": solved_count,
        "total_count": total_count,
        "completion_percentage": round(completion_percentage, 2)
    }

@app.get("/task/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: int):
    return templates.TemplateResponse("task_detail.html", {"request": request, "task_id": task_id})

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    result_schema = get_result_schema_for_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    progress = db.query(UserProgressModel).filter(
        UserProgressModel.user_id == current_user.id,
        UserProgressModel.task_id == task.id
    ).first()

    is_solved = progress.solved if progress else False

    schema_tables = db.query(SchemaTableModel).filter(SchemaTableModel.task_id == task_id).all()
    schema_info = []

    for table in schema_tables:
        columns = db.query(SchemaColumnModel).filter(SchemaColumnModel.table_id == table.id).all()

        columns_data = [
            {
                "name": column.name,
                "type": column.type,
                "constraints": column.constraints
            }
            for column in columns
        ]

        schema_info.append({
            "table_name": table.table_name,
            "columns": columns_data
        })

    columns_info = TASK_COLUMNS_INFO.get(task_id, "")

    return {
        "id": task.id,
        "name": task.name,
        "difficulty": task.difficulty,
        "description": task.description,
        "solved": is_solved,
        "schema": schema_info,
        "result_schema": result_schema,
        "columns_info": columns_info,
    }

@app.post("/api/tasks/{task_id}/run")
async def run_query(
    task_id: int,
    query_data: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    test_engine = Depends(get_test_engine)
):
    sql_query = query_data.get("query", "")

    if not sql_query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Проверяем безопасность запроса
    is_safe, error_message = is_query_safe(sql_query, task_id)
    if not is_safe:
        return {"success": False, "message": error_message}

    # Получаем информацию о требуемых столбцах
    columns_info = TASK_COLUMNS_INFO.get(task_id, "")

    # Выполняем запрос на тестовой БД
    try:
        results_list, error = execute_query(sql_query, test_engine)

        if error:
            # Возвращаем ошибку и информацию о столбцах пользователю
            return {
                "success": False,
                "message": f"Query execution error: {error}. {columns_info}"
            }

        # Проверяем соответствие столбцов
        if results_list:
            try:
                mock_result = db.query(MockResultModel).filter(MockResultModel.task_id == task_id).first()
                if mock_result:
                    expected_results = json.loads(mock_result.result_data)
                    if expected_results:
                        actual_keys = set(k.lower() for k in results_list[0].keys())
                        expected_keys = set(k.lower() for k in expected_results[0].keys())

                        if actual_keys != expected_keys:
                            # Находим отличия
                            missing = sorted(expected_keys - actual_keys)
                            extra = sorted(actual_keys - expected_keys)

                            warning_message = f"Внимание! {columns_info}"
                            if missing:
                                warning_message += f" Отсутствуют столбцы: {', '.join(missing)}."
                            if extra:
                                warning_message += f" Лишние столбцы: {', '.join(extra)}."

                            return {
                                "success": True,
                                "results": results_list,
                                "warning": warning_message
                            }
            except Exception as column_err:
                pass

        return {"success": True, "results": results_list}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Failed to execute query: {str(e)}", "columns_info": columns_info}



@app.post("/api/tasks/{task_id}/submit")
async def submit_solution(
    task_id: int,
    solution_data: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    test_engine = Depends(get_test_engine)
):
    try:
        sql_query = solution_data.get("query", "")

        if not sql_query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        is_safe, error_message = is_query_safe(sql_query, task_id)
        if not is_safe:
            return {"success": False, "message": error_message}

        columns_info = TASK_COLUMNS_INFO.get(task_id, "")

        mock_result = db.query(MockResultModel).filter(MockResultModel.task_id == task_id).first()
        if not mock_result:
            return {"success": False, "message": "No expected results found for this task"}

        # Выполняем запрос на тестовой БД
        actual_results, error = execute_query(sql_query, test_engine)

        if error:
            return {
                "success": False,
                "message": f"Query execution error: {error}. {columns_info}"
            }

        # Парсим эталонные результаты из JSON
        expected_results = json.loads(mock_result.result_data)

        # Проверяем соответствие столбцов перед сравнением данных
        if actual_results and expected_results:
            actual_keys = set(k.lower() for k in actual_results[0].keys())
            expected_keys = set(k.lower() for k in expected_results[0].keys())

            if actual_keys != expected_keys:
                # Находим отличия
                missing = sorted(expected_keys - actual_keys)
                extra = sorted(actual_keys - expected_keys)

                error_message = f"Результат запроса имеет неверные столбцы. {columns_info}"
                if missing:
                    error_message += f" Отсутствуют столбцы: {', '.join(missing)}."
                if extra:
                    error_message += f" Лишние столбцы: {', '.join(extra)}."

                return {"success": False, "message": error_message}

        is_correct = compare_results(actual_results, expected_results)
        if not is_correct:
            error_message = f"Результат вашего запроса не соответствует ожидаемому. Пожалуйста, проверьте: 1) Правильность имен столбцов ({columns_info}); 2) Данные и их форматы; 3) Порядок сортировки, если требуется."

            return {"success": False, "message": error_message}

        progress = db.query(UserProgressModel).filter(
            UserProgressModel.user_id == current_user.id,
            UserProgressModel.task_id == task_id
        ).first()

        if not progress:
            try:
                max_id_result = db.query(func.max(UserProgressModel.id)).scalar()
                next_id = 1 if max_id_result is None else max_id_result + 1
            except Exception as e:
                next_id = 1

            progress = UserProgressModel(
                id=next_id,
                user_id=current_user.id,
                task_id=task_id,
                solved=True
            )
            db.add(progress)
        else:
            progress.solved = True

        db.commit()

        return {"success": True, "message": "Your solution is correct!"}

    except HTTPException as he:
        raise he

    except Exception as e:
        print(f"Error submitting solution: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "message": f"An error occurred while processing your query. Please check your SQL syntax and that all required columns ({columns_info}) are included."
        }



@app.get("/api/user/current")
async def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "is_admin": current_user.get("is_admin", False),
    }

@app.get("/api/admin/tables")
async def get_available_tables(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

    # In a real app, this would query your database system
    # Here we're using mock data
    available_tables = [
        {
            "name": "employees",
            "columns": [
                {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                {"name": "department_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                {"name": "salary", "type": "DECIMAL(10,2)", "constraints": ""},
                {"name": "hire_date", "type": "DATE", "constraints": ""},
            ]
        },
        {
            "name": "departments",
            "columns": [
                {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                {"name": "location", "type": "VARCHAR(100)", "constraints": ""},
            ]
        },
        {
            "name": "projects",
            "columns": [
                {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                {"name": "start_date", "type": "DATE", "constraints": ""},
                {"name": "end_date", "type": "DATE", "constraints": ""},
            ]
        },
        {
            "name": "employee_projects",
            "columns": [
                {"name": "employee_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                {"name": "project_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                {"name": "role", "type": "VARCHAR(100)", "constraints": ""},
            ]
        },
        {
            "name": "sales",
            "columns": [
                {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                {"name": "product_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                {"name": "customer_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                {"name": "sale_date", "type": "DATE", "constraints": "NOT NULL"},
                {"name": "quantity", "type": "INTEGER", "constraints": "NOT NULL"},
                {"name": "amount", "type": "DECIMAL(10,2)", "constraints": "NOT NULL"},
            ]
        }
    ]

    return available_tables

@app.post("/api/admin/tasks")
async def create_task(
    task_data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate required fields
    required_fields = ["name", "description", "difficulty", "solution_query", "tables"]
    for field in required_fields:
        if field not in task_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # Create new task ID
    task_id = len(tasks_db) + 1

    # Add new task to tasks_db
    new_task = {
        "id": task_id,
        "name": task_data["name"],
        "description": task_data["description"],
        "difficulty": task_data["difficulty"],
        "solution_query": task_data["solution_query"],
        "tables": task_data["tables"]
    }

    tasks_db.append(new_task)

    return {"success": True, "task_id": task_id}

@app.post("/api/admin/run-query")
async def run_admin_query(
    query_data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Требуются права админа")

    sql_query = query_data.get("query", "")
    selected_tables = query_data.get("tables", [])

    if not sql_query.strip():
        raise HTTPException(status_code=400, detail="Запрос не может быть пустым")

    # In a real application, you would:
    # 1. Validate the SQL for security
    # 2. Run it against a test database with the selected tables
    # 3. Return the results

    # For this demo, we'll simulate query execution with mock data
    try:
        # This is a simulated function that would normally execute the SQL
        results = simulate_admin_query_execution(sql_query, selected_tables)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

def simulate_admin_query_execution(query, selected_tables):
    # Very basic SQL validation
    if "drop" in query.lower() or "delete" in query.lower() or "update" in query.lower() or "insert" in query.lower():
        raise Exception("Only SELECT statements are allowed")

    # Generate a sample result set based on the query and selected tables
    # In a real application, this would execute the query against a database

    # Mock data generation based on tables
    if not selected_tables:
        return []

    # Create mock results - simple demonstration data
    columns = []
    data = []

    # Generate some sample data based on the tables
    if "employees" in selected_tables:
        columns = ["id", "name", "department_id", "salary", "hire_date"]
        data = [
            {"id": 1, "name": "John Doe", "department_id": 1, "salary": 5000, "hire_date": "2020-01-15"},
            {"id": 2, "name": "Jane Smith", "department_id": 2, "salary": 6000, "hire_date": "2019-05-20"},
            {"id": 3, "name": "Bob Johnson", "department_id": 1, "salary": 4500, "hire_date": "2021-03-10"}
        ]
    elif "departments" in selected_tables:
        columns = ["id", "name", "location"]
        data = [
            {"id": 1, "name": "Engineering", "location": "New York"},
            {"id": 2, "name": "Marketing", "location": "San Francisco"},
            {"id": 3, "name": "HR", "location": "Chicago"}
        ]
    elif "sales" in selected_tables:
        columns = ["id", "product_id", "customer_id", "sale_date", "quantity", "amount"]
        data = [
            {"id": 1, "product_id": 101, "customer_id": 201, "sale_date": "2023-01-15", "quantity": 2, "amount": 120.50},
            {"id": 2, "product_id": 102, "customer_id": 202, "sale_date": "2023-01-20", "quantity": 1, "amount": 85.99},
            {"id": 3, "product_id": 101, "customer_id": 203, "sale_date": "2023-02-05", "quantity": 3, "amount": 180.75}
        ]

    return data

@app.get("/admin/create-task", response_class=HTMLResponse)
async def admin_create_task(request: Request):
    return templates.TemplateResponse("admin_create_task.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
