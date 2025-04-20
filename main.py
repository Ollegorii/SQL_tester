from fastapi import FastAPI, Request, HTTPException, Depends, status, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Mock database
users_db = {-1: {"id": -1, "username": "admin", "email": "admin@admin.com", "password": "admin", "is_admin": True}}
tasks_db = [
    {"id": 1, "name": "Select all employees", "difficulty": "Easy", "description": "Write a query to select all employees from the employees table."},
    {"id": 2, "name": "Count by department", "difficulty": "Easy", "description": "Count the number of employees in each department."},
    {"id": 3, "name": "Complex join with filter", "difficulty": "Medium", "description": "Join multiple tables and filter the results based on conditions."},
    {"id": 4, "name": "Window functions", "difficulty": "Hard", "description": "Use window functions to calculate running totals."},
    {"id": 5, "name": "Recursive CTE", "difficulty": "Hard", "description": "Write a recursive common table expression to solve a hierarchical problem."},
]

user_progress = {-1: {task["id"]: False for task in tasks_db}}  # user_id -> {task_id: True/False}

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

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

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None or user_id not in users_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return users_db[user_id]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/register")
async def register(user: UserCreate):
    if any(u["username"] == user.username for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Username already registered")

    if any(u["email"] == user.email for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password": user.password
    }

    user_progress[user_id] = {task["id"]: False for task in tasks_db}

    return {"message": "User registered successfully"}

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_id = None
    for uid, user in users_db.items():
        if user["username"] == form_data.username and user["password"] == form_data.password:
            user_id = uid
            break

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/tasks")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    user_tasks = []

    for task in tasks_db:
        task_with_status = {
            "id": task["id"],
            "name": task["name"],
            "difficulty": task["difficulty"],
            "solved": user_progress[user_id].get(task["id"], False)
        }
        user_tasks.append(task_with_status)

    return user_tasks

@app.get("/api/user/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    user_task_progress = user_progress.get(user_id, {})

    solved_count = sum(1 for solved in user_task_progress.values() if solved)
    total_count = len(tasks_db)

    if total_count > 0:
        completion_percentage = (solved_count / total_count) * 100
    else:
        completion_percentage = 0

    return {
        "solved_count": solved_count,
        "total_count": total_count,
        "completion_percentage": round(completion_percentage, 2)
    }

@app.post("/api/tasks/{task_id}/solve")
async def solve_task(task_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    task_exists = any(task["id"] == task_id for task in tasks_db)
    if not task_exists:
        raise HTTPException(status_code=404, detail="Task not found")

    if user_id not in user_progress:
        user_progress[user_id] = {}

    user_progress[user_id][task_id] = True

    return {"message": "Task marked as solved"}

@app.get("/task/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: int):
    return templates.TemplateResponse("task_detail.html", {"request": request, "task_id": task_id})

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    task = next((task for task in tasks_db if task["id"] == task_id), None)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    user_id = current_user["id"]

    is_solved = user_progress.get(user_id, {}).get(task_id, False)

    schema_info = get_schema_for_task(task_id)
    result_schema = get_result_schema_for_task(task_id)

    return {
        "id": task["id"],
        "name": task["name"],
        "difficulty": task["difficulty"],
        "description": task["description"],
        "solved": is_solved,
        "schema": schema_info,
        "result_schema": result_schema,
    }

@app.post("/api/tasks/{task_id}/run")
async def run_query(
    task_id: int,
    query_data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    sql_query = query_data.get("query", "")

    if not sql_query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # mocked
    try:
        results = simulate_query_execution(task_id, sql_query)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/tasks/{task_id}/submit")
async def submit_solution(
    task_id: int,
    solution_data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    sql_query = solution_data.get("query", "")

    if not sql_query.strip():
        raise HTTPException(status_code=400, detail="Solution cannot be empty")

    # mocked
    try:
        user_id = current_user["id"]
        if user_id not in user_progress:
            user_progress[user_id] = {}

        user_progress[user_id][task_id] = True

        return {"success": True, "message": "Your solution is correct!"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_schema_for_task(task_id):
    # mocked
    schemas = {
        1: [
            {
                "table_name": "employees",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "department_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "salary", "type": "DECIMAL(10,2)", "constraints": ""},
                    {"name": "hire_date", "type": "DATE", "constraints": ""},
                ]
            }
        ],
        2: [
            {
                "table_name": "employees",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "department_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "salary", "type": "DECIMAL(10,2)", "constraints": ""},
                    {"name": "hire_date", "type": "DATE", "constraints": ""},
                ]
            },
            {
                "table_name": "departments",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "location", "type": "VARCHAR(100)", "constraints": ""},
                ]
            }
        ],
        3: [
            {
                "table_name": "employees",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "department_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "salary", "type": "DECIMAL(10,2)", "constraints": ""},
                    {"name": "hire_date", "type": "DATE", "constraints": ""},
                ]
            },
            {
                "table_name": "departments",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "location", "type": "VARCHAR(100)", "constraints": ""},
                ]
            },
            {
                "table_name": "projects",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "start_date", "type": "DATE", "constraints": ""},
                    {"name": "end_date", "type": "DATE", "constraints": ""},
                ]
            },
            {
                "table_name": "employee_projects",
                "columns": [
                    {"name": "employee_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "project_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "role", "type": "VARCHAR(100)", "constraints": ""},
                ]
            }
        ],
        4: [
            {
                "table_name": "sales",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "product_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "customer_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "sale_date", "type": "DATE", "constraints": "NOT NULL"},
                    {"name": "quantity", "type": "INTEGER", "constraints": "NOT NULL"},
                    {"name": "amount", "type": "DECIMAL(10,2)", "constraints": "NOT NULL"},
                ]
            },
            {
                "table_name": "products",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "category", "type": "VARCHAR(100)", "constraints": ""},
                    {"name": "price", "type": "DECIMAL(10,2)", "constraints": "NOT NULL"},
                ]
            },
            {
                "table_name": "customers",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "email", "type": "VARCHAR(100)", "constraints": ""},
                    {"name": "region", "type": "VARCHAR(100)", "constraints": ""},
                ]
            }
        ],
        5: [
            {
                "table_name": "employees",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                    {"name": "manager_id", "type": "INTEGER", "constraints": "FOREIGN KEY (self-reference)"},
                    {"name": "department_id", "type": "INTEGER", "constraints": "FOREIGN KEY"},
                    {"name": "salary", "type": "DECIMAL(10,2)", "constraints": ""},
                    {"name": "level", "type": "INTEGER", "constraints": ""},
                ]
            },
            {
                "table_name": "departments",
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(100)", "constraints": "NOT NULL"},
                ]
            }
        ]
    }
    return schemas.get(task_id, [])

def simulate_query_execution(task_id, query):
    mock_results = {
        1: [
            {"id": 1, "name": "John Doe", "department_id": 1, "salary": 5000, "hire_date": "2020-01-15"},
            {"id": 2, "name": "Jane Smith", "department_id": 2, "salary": 6000, "hire_date": "2019-05-20"},
            {"id": 3, "name": "Bob Johnson", "department_id": 1, "salary": 4500, "hire_date": "2021-03-10"},
        ],
        2: [
            {"department_id": 1, "department_name": "Engineering", "count": 15},
            {"department_id": 2, "department_name": "Marketing", "count": 8},
            {"department_id": 3, "department_name": "HR", "count": 5},
            {"department_id": 4, "department_name": "Finance", "count": 7},
        ],
        3: [
            {"employee_name": "John Doe", "department_name": "Engineering", "project_count": 3},
            {"employee_name": "Jane Smith", "department_name": "Marketing", "project_count": 2},
            {"employee_name": "Bob Johnson", "department_name": "Engineering", "project_count": 1},
        ],
        4: [
            {"month": "2023-01", "product": "Laptop", "total_sales": 45000, "running_total": 45000},
            {"month": "2023-02", "product": "Laptop", "total_sales": 52000, "running_total": 97000},
            {"month": "2023-03", "product": "Laptop", "total_sales": 48000, "running_total": 145000},
        ],
        5: [
            {"employee_name": "John Doe", "level": 1, "manager_name": None},
            {"employee_name": "Jane Smith", "level": 2, "manager_name": "John Doe"},
            {"employee_name": "Bob Johnson", "level": 3, "manager_name": "Jane Smith"},
        ]
    }
    return mock_results.get(task_id, [])

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

@app.get("/api/user/current")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
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
