from fastapi import FastAPI, Request, HTTPException, Depends, status, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import func
import pandas as pd

# Импортируем модели из db_init
from db_init import Base, UserModel, TaskModel, SchemaTableModel, SchemaColumnModel, UserProgressModel, MockResultModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Настройки базы данных Oracle с cx_oracle
DB_URL = "oracle+cx_oracle://USER_APP:maksim2003@158.160.94.135:1521/XE"
TEST_DB_URL = "oracle+cx_oracle://USER_APP:maksim2003@158.160.94.135:1521/XE"  # Тестовая БД для проверки запросов

# Создаем движок SQLAlchemy
engine = create_engine(DB_URL)
test_engine = create_engine(TEST_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройки JWT
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic модели
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    username: str
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskResponse(BaseModel):
    id: int
    name: str
    difficulty: str
    solved: bool = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Зависимость для получения движка тестовой БД
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
        # Создаем соединение с помощью engine
        with engine.connect() as connection:
            # Используем text() для создания SQL выражения
            sql = text(query)
            # Выполняем запрос и получаем результат
            result = connection.execute(sql)
            # Получаем имена столбцов
            column_names = [str(col).lower() for col in result.keys()]
            
            # Получаем данные
            rows = result.fetchall()
            
            # Создаем список словарей для безопасной сериализации в JSON
            data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    # Безопасно преобразуем все значения в строки
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
    """Сравнивает полученный результат с эталонным"""
    if actual_results is None or expected_data is None:
        return False
    
    try:
        # Проверяем, что количество записей совпадает
        if len(actual_results) != len(expected_data):
            print(f"Row count mismatch: actual {len(actual_results)}, expected {len(expected_data)}")
            return False
        
        # Если результаты пустые, считаем совпадением
        if len(actual_results) == 0 and len(expected_data) == 0:
            return True
        
        # Проверяем, что наборы столбцов совпадают (игнорируя регистр)
        actual_keys = set(k.lower() for k in actual_results[0].keys())
        expected_keys = set(k.lower() for k in expected_data[0].keys())
        
        if actual_keys != expected_keys:
            print(f"Column mismatch:")
            print(f"  Actual columns: {sorted(actual_keys)}")
            print(f"  Expected columns: {sorted(expected_keys)}")
            print(f"  Missing in actual: {sorted(expected_keys - actual_keys)}")
            print(f"  Extra in actual: {sorted(actual_keys - expected_keys)}")
            return False
        
        # Создаем нормализованные копии для сравнения
        normalized_actual = []
        for row in actual_results:
            new_row = {}
            for key in row.keys():
                value = row[key]
                # Для дат оставляем только часть "YYYY-MM-DD"
                if value is not None and 'date' in key.lower() and isinstance(value, str) and ' ' in value:
                    value = value.split(' ')[0]
                new_row[key.lower()] = str(value) if value is not None else None
            normalized_actual.append(new_row)
        
        normalized_expected = []
        for row in expected_data:
            new_row = {}
            for key in row.keys():
                value = row[key]
                # Для дат оставляем только часть "YYYY-MM-DD"
                if value is not None and 'date' in key.lower() and isinstance(value, str) and len(value) > 10:
                    value = value[:10]
                new_row[key.lower()] = str(value) if value is not None else None
            normalized_expected.append(new_row)
        
        # Сортируем результаты для корректного сравнения
        # Используем все ключи для сортировки
        all_keys = sorted(expected_keys)
        
        def sort_key(row):
            return tuple(str(row.get(key, "")) for key in all_keys)
        
        sorted_actual = sorted(normalized_actual, key=sort_key)
        sorted_expected = sorted(normalized_expected, key=sort_key)
        
        # Проверка, что каждая строка совпадает
        for i, (actual_row, expected_row) in enumerate(zip(sorted_actual, sorted_expected)):
            if actual_row != expected_row:
                print(f"Row {i} mismatch:")
                for key in all_keys:
                    if actual_row.get(key) != expected_row.get(key):
                        print(f"  Key '{key}':")
                        print(f"    Actual: {actual_row.get(key)}")
                        print(f"    Expected: {expected_row.get(key)}")
                return False
        
        return True
    except Exception as e:
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
        # Проверка на уникальность имени пользователя
        existing_user = db.query(UserModel).filter(UserModel.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Проверка на уникальность email
        existing_email = db.query(UserModel).filter(UserModel.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Создаем нового пользователя
        user_id = str(uuid.uuid4())
        new_user = UserModel(
            id=user_id,
            username=user.username,
            email=user.email,
            password=user.password  # В реальном приложении здесь должно быть хеширование
        )
        
        db.add(new_user)
        db.commit()
        
        # Инициализируем прогресс пользователя для всех существующих задач
        tasks = db.query(TaskModel).all()
        
        # Безопасное получение следующего ID
        try:
            # Исправленное получение max ID
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
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        # Логируем неожиданные ошибки и возвращаем 500
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
    # Получаем все задачи
    tasks = db.query(TaskModel).all()
    
    # Получаем прогресс текущего пользователя
    user_progress_records = db.query(UserProgressModel).filter(
        UserProgressModel.user_id == current_user.id
    ).all()
    
    # Создаем словарь {task_id: solved}
    progress_dict = {record.task_id: record.solved for record in user_progress_records}
    
    # Формируем список задач с информацией о прогрессе
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
    # Получаем количество решенных задач
    solved_count = db.query(UserProgressModel).filter(
        UserProgressModel.user_id == current_user.id,
        UserProgressModel.solved == True
    ).count()
    
    # Получаем общее количество задач
    total_count = db.query(TaskModel).count()
    
    # Расчет процента выполнения
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
    # Получаем задачу по ID
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Получаем информацию о том, решена ли задача пользователем
    progress = db.query(UserProgressModel).filter(
        UserProgressModel.user_id == current_user.id,
        UserProgressModel.task_id == task.id
    ).first()
    
    is_solved = progress.solved if progress else False
    
    # Получаем схему для задачи
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
    
    return {
        "id": task.id,
        "name": task.name,
        "difficulty": task.difficulty,
        "description": task.description,
        "solved": is_solved,
        "schema": schema_info
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
    
    # Выполняем запрос на тестовой БД
    try:
        results_list, error = execute_query(sql_query, test_engine)
        
        if error:
            return {"success": False, "error": f"Query execution error: {error}"}
        
        # Возвращаем результаты напрямую, так как они уже в формате списка словарей
        return {"success": True, "results": results_list}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Failed to execute query: {str(e)}"}


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
        
        # Получаем мок-результаты из БД
        mock_result = db.query(MockResultModel).filter(MockResultModel.task_id == task_id).first()
        if not mock_result:
            return {"success": False, "error": "No expected results found for this task"}
        
        # Выполняем запрос на тестовой БД
        actual_results, error = execute_query(sql_query, test_engine)
        
        if error:
            return {"success": False, "error": f"Query execution error: {error}"}
        
        # Парсим эталонные результаты из JSON
        expected_results = json.loads(mock_result.result_data)
        
        # Сравниваем полученные результаты с эталонными
        is_correct = compare_results(actual_results, expected_results)
        print(actual_results)
        print(expected_results)
        if not is_correct:
            return {"success": False, "message": "Your solution is incorrect. The results do not match the expected output."}
        
        # Обновляем прогресс пользователя, если решение верное
        progress = db.query(UserProgressModel).filter(
            UserProgressModel.user_id == current_user.id,
            UserProgressModel.task_id == task_id
        ).first()
        
        if not progress:
            # Если записи нет, создаем новую с автогенерируемым ID
            try:
                # Исправленное получение max ID
                max_id_result = db.query(func.max(UserProgressModel.id)).scalar()
                next_id = 1 if max_id_result is None else max_id_result + 1
            except Exception as e:
                print(f"Error getting max ID: {e}")
                next_id = 1
            
            progress = UserProgressModel(
                id=next_id,
                user_id=current_user.id,
                task_id=task_id,
                solved=True
            )
            db.add(progress)
        else:
            # Иначе обновляем существующую
            progress.solved = True
        
        db.commit()
        
        return {"success": True, "message": "Your solution is correct!"}
    
    except HTTPException:
        # Пробрасываем HTTP исключения
        raise
    
    except Exception as e:
        # Логируем и возвращаем внутренние ошибки
        print(f"Error submitting solution: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/api/user/current")
async def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
