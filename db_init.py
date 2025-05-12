import os
import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, Float, Date, ForeignKey, Table, MetaData, Sequence, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import uuid
import cx_Oracle

# Настройки базы данных Oracle с cx_oracle
DB_URL = "oracle+cx_oracle://USER_APP:maksim2003@51.250.100.249:1521/XE"

# Создаем движок SQLAlchemy
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определение моделей данных
class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))
    is_admin = Column(Boolean, default=False)

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    difficulty = Column(String(50))
    description = Column(Text)

class SchemaTableModel(Base):
    __tablename__ = "schema_tables"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    table_name = Column(String(100))

class SchemaColumnModel(Base):
    __tablename__ = "schema_columns"

    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("schema_tables.id"))
    name = Column(String(100))
    type = Column(String(100))
    constraints = Column(String(200))

class UserProgressModel(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    solved = Column(Boolean, default=False)

class MockResultModel(Base):
    __tablename__ = "mock_results"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    result_data = Column(Text)  # JSON строка с мок-результатами

class ResultSchemaModel(Base):
    __tablename__ = "result_schemas"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    name = Column(String(100))
    type = Column(String(100))
    description = Column(String(200))

def drop_all_tables():
    """Удаляет все таблицы из БД"""
    connection = engine.connect()

    # Список таблиц для удаления
    tables = [
        "user_progress",
        "mock_results",
        "schema_columns",
        "schema_tables",
        "result_schemas", # Добавлена новая таблица
        "tasks",
        "users"
    ]

    for table in tables:
        try:
            connection.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
            print(f"Table {table} dropped")
        except Exception as e:
            print(f"Error dropping table {table}: {e}")

    connection.close()

def create_tables():
    """Создает все таблицы в БД"""
    Base.metadata.create_all(bind=engine)
    print("All tables created")

def create_test_tables():
    """Создает тестовые таблицы с данными для выполнения SQL-запросов"""
    print("Starting test tables creation...")

    # Создаем отдельное соединение напрямую через cx_Oracle
    try:
        dsn = cx_Oracle.makedsn("51.250.96.36", 1521, service_name="XE")
        conn = cx_Oracle.connect(user="USER_APP", password="maksim2003", dsn=dsn)
        cursor = conn.cursor()

        # Удаляем тестовые таблицы, если они существуют
        tables_to_drop = [
            "sales", "employee_projects", "projects", "products",
            "customers", "employees", "departments"
        ]

        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
                print(f"Test table {table} dropped")
            except:
                print(f"Table {table} did not exist, continuing...")

        # Создаем таблицы в соответствии со схемами заданий

        # 1. Таблица departments
        cursor.execute("""
        CREATE TABLE departments (
            id NUMBER(10) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            location VARCHAR2(100)
        )
        """)
        print("Created table departments")

        # 2. Таблица employees - строго по схеме задания 1
        cursor.execute("""
        CREATE TABLE employees (
            id NUMBER(10) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            department_id NUMBER(10),
            salary NUMBER(10,2),
            hire_date DATE
        )
        """)
        print("Created table employees")

        # Добавляем внешний ключ на departments
        try:
            cursor.execute("""
            ALTER TABLE employees
            ADD CONSTRAINT fk_dept
            FOREIGN KEY (department_id)
            REFERENCES departments(id)
            """)
            print("Added foreign key constraint to employees")
        except Exception as e:
            print(f"Warning: Could not add foreign key constraint: {e}")

        # 3. Остальные таблицы - без изменений
        # Таблица projects
        cursor.execute("""
        CREATE TABLE projects (
            id NUMBER(10) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            start_date DATE,
            end_date DATE
        )
        """)
        print("Created table projects")

        # Таблица employee_projects
        cursor.execute("""
        CREATE TABLE employee_projects (
            employee_id NUMBER(10),
            project_id NUMBER(10),
            role VARCHAR2(100),
            PRIMARY KEY (employee_id, project_id),
            CONSTRAINT fk_emp FOREIGN KEY (employee_id) REFERENCES employees(id),
            CONSTRAINT fk_proj FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """)
        print("Created table employee_projects")

        # Таблица products
        cursor.execute("""
        CREATE TABLE products (
            id NUMBER(10) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            category VARCHAR2(100),
            price NUMBER(10,2) NOT NULL
        )
        """)
        print("Created table products")

        # Таблица customers
        cursor.execute("""
        CREATE TABLE customers (
            id NUMBER(10) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            email VARCHAR2(100),
            region VARCHAR2(100)
        )
        """)
        print("Created table customers")

        # Таблица sales
        cursor.execute("""
        CREATE TABLE sales (
            id NUMBER(10) PRIMARY KEY,
            product_id NUMBER(10),
            customer_id NUMBER(10),
            sale_date DATE NOT NULL,
            quantity NUMBER(10) NOT NULL,
            amount NUMBER(10,2) NOT NULL,
            CONSTRAINT fk_prod FOREIGN KEY (product_id) REFERENCES products(id),
            CONSTRAINT fk_cust FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """)
        print("Created table sales")

        # Заполняем таблицы тестовыми данными
        # Departments
        departments = [
            (1, 'Engineering', 'Building A'),
            (2, 'Marketing', 'Building B'),
            (3, 'HR', 'Building A'),
            (4, 'Finance', 'Building C')
        ]

        for dept in departments:
            cursor.execute(f"""
            INSERT INTO departments (id, name, location)
            VALUES ({dept[0]}, '{dept[1]}', '{dept[2]}')
            """)
        print("Inserted data into departments")

        # Employees - вставляем данные, которые имитируют иерархию через department_id
        # Для задачи 5 мы будем использовать department_id как способ определения уровня
        # и связь между сотрудниками
        employees = [
            # id, name, department_id (будет использоваться как "level"), salary, hire_date
            (1, 'John Doe', 1, 5000, '2020-01-15'),       # CEO (department 1 = Engineering)
            (2, 'Jane Smith', 1, 6000, '2019-05-20'),     # Manager под John (Engineering)
            (3, 'Bob Johnson', 1, 4500, '2021-03-10'),    # Employee под Jane (Engineering)
            (4, 'Alice Brown', 1, 5500, '2018-11-01'),    # Manager под John (Engineering)
            (5, 'Charlie Wilson', 1, 4800, '2021-07-15'), # Employee под Bob (Engineering)
            (6, 'Dave Miller', 2, 6500, '2017-09-20'),    # Manager под John (Marketing)
            (7, 'Eve Davis', 2, 5200, '2020-04-12'),      # Employee под Jane (Marketing)
            (8, 'Frank White', 2, 4900, '2021-01-25'),    # Employee под Bob (Marketing)
            (9, 'Grace Taylor', 3, 5300, '2019-08-05'),   # Employee под Alice (HR)
            (10, 'Henry Martin', 3, 6200, '2018-03-15')   # Employee под Dave (HR)
        ]

        for emp in employees:
            cursor.execute(f"""
            INSERT INTO employees (id, name, department_id, salary, hire_date)
            VALUES ({emp[0]}, '{emp[1]}', {emp[2]}, {emp[3]}, TO_DATE('{emp[4]}', 'YYYY-MM-DD'))
            """)
        print("Inserted data into employees")

        # Остальные данные - без изменений
        # Projects
        projects = [
            (1, 'Website Redesign', '2022-01-01', '2022-03-15'),
            (2, 'Mobile App', '2022-02-15', '2022-06-30'),
            (3, 'Database Migration', '2022-04-01', '2022-08-15'),
            (4, 'Cloud Migration', '2022-05-15', '2022-12-31')
        ]

        for proj in projects:
            cursor.execute(f"""
            INSERT INTO projects (id, name, start_date, end_date)
            VALUES ({proj[0]}, '{proj[1]}',
                TO_DATE('{proj[2]}', 'YYYY-MM-DD'),
                TO_DATE('{proj[3]}', 'YYYY-MM-DD'))
            """)
        print("Inserted data into projects")

        # Employee Projects
        emp_projects = [
            (1, 1, 'Lead'),
            (2, 1, 'Designer'),
            (3, 1, 'Developer'),
            (1, 2, 'Consultant'),
            (2, 2, 'Lead'),
            (5, 2, 'Developer'),
            (1, 3, 'Reviewer'),
            (3, 3, 'Developer'),
            (6, 3, 'Lead'),
            (7, 4, 'Designer'),
            (8, 4, 'Developer'),
            (6, 4, 'Reviewer')
        ]

        for ep in emp_projects:
            cursor.execute(f"""
            INSERT INTO employee_projects (employee_id, project_id, role)
            VALUES ({ep[0]}, {ep[1]}, '{ep[2]}')
            """)
        print("Inserted data into employee_projects")

        # Products
        products = [
            (1, 'Laptop', 'Electronics', 1200.00),
            (2, 'Smartphone', 'Electronics', 800.00),
            (3, 'Chair', 'Furniture', 150.00),
            (4, 'Desk', 'Furniture', 250.00),
            (5, 'Headphones', 'Electronics', 80.00)
        ]

        for prod in products:
            cursor.execute(f"""
            INSERT INTO products (id, name, category, price)
            VALUES ({prod[0]}, '{prod[1]}', '{prod[2]}', {prod[3]})
            """)
        print("Inserted data into products")

        # Customers
        customers = [
            (1, 'Acme Corp', 'acme@example.com', 'North'),
            (2, 'XYZ Industries', 'xyz@example.com', 'South'),
            (3, 'Global Services', 'global@example.com', 'East'),
            (4, 'Local Business', 'local@example.com', 'West'),
            (5, 'Super Retail', 'super@example.com', 'North')
        ]

        for cust in customers:
            cursor.execute(f"""
            INSERT INTO customers (id, name, email, region)
            VALUES ({cust[0]}, '{cust[1]}', '{cust[2]}', '{cust[3]}')
            """)
        print("Inserted data into customers")

        # Sales (с данными по месяцам для задач с оконными функциями)
        sales_data = [
            # 2023-01
            (1, 1, 1, '2023-01-05', 5, 6000.00),
            (2, 2, 2, '2023-01-10', 3, 2400.00),
            (3, 1, 3, '2023-01-15', 2, 2400.00),
            (4, 3, 4, '2023-01-20', 10, 1500.00),
            (5, 5, 5, '2023-01-25', 15, 1200.00),
            # 2023-02
            (6, 1, 2, '2023-02-05', 7, 8400.00),
            (7, 2, 1, '2023-02-10', 4, 3200.00),
            (8, 4, 3, '2023-02-15', 3, 750.00),
            (9, 5, 4, '2023-02-20', 20, 1600.00),
            (10, 3, 5, '2023-02-25', 5, 750.00),
            # 2023-03
            (11, 1, 3, '2023-03-05', 6, 7200.00),
            (12, 2, 2, '2023-03-10', 5, 4000.00),
            (13, 3, 1, '2023-03-15', 8, 1200.00),
            (14, 4, 5, '2023-03-20', 4, 1000.00),
            (15, 5, 4, '2023-03-25', 12, 960.00)
        ]

        for sale in sales_data:
            cursor.execute(f"""
            INSERT INTO sales (id, product_id, customer_id, sale_date, quantity, amount)
            VALUES ({sale[0]}, {sale[1]}, {sale[2]},
                TO_DATE('{sale[3]}', 'YYYY-MM-DD'), {sale[4]}, {sale[5]})
            """)
        print("Inserted data into sales")

        conn.commit()
        print("Test tables created and populated successfully")

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error creating test tables: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        print("Test tables creation process completed")

def init_data():
    """Инициализирует данные в таблицах"""
    # Полностью сбрасываем базу данных
    try:
        drop_all_tables()
        time.sleep(1)  # Небольшая задержка для уверенности
    except Exception as e:
        print(f"Error during database reset: {e}")

    # Создаем таблицы заново
    create_tables()
    time.sleep(1)  # Небольшая задержка для уверенности

    db = SessionLocal()
    try:
        # Создаем admin пользователя
        admin_user = UserModel(
            id="-1",
            username="admin",
            email="admin@admin.com",
            password="admin",
            is_admin=True
        )

        db.add(admin_user)
        db.commit()
        print("Admin user created")

        # Добавляем задачи
        tasks = [
            {"id": 1, "name": "Select all employees", "difficulty": "Easy",
            "description": "Write a query to select all employees from the employees table."},
            {"id": 2, "name": "Count by department", "difficulty": "Easy",
            "description": "Count the number of employees in each department."},
            {"id": 3, "name": "Complex join with filter", "difficulty": "Medium",
            "description": "Join multiple tables and filter the results based on conditions."},
            {"id": 4, "name": "Window functions", "difficulty": "Hard",
            "description": "Use window functions to calculate running totals."},
            {"id": 5, "name": "Recursive CTE", "difficulty": "Hard",
            "description": "Write a recursive common table expression to solve a hierarchical problem."},
        ]

        for task_data in tasks:
            task = TaskModel(**task_data)
            db.add(task)

        db.commit()
        print("Tasks created")

        # Добавляем схемы для задач
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
            ]
        }

        # Глобальные счетчики для ID
        table_id = 1
        column_id = 1

        for task_id, tables in schemas.items():
            for table_data in tables:
                schema_table = SchemaTableModel(
                    id=table_id,
                    task_id=task_id,
                    table_name=table_data["table_name"]
                )
                db.add(schema_table)
                db.flush()

                for column_data in table_data["columns"]:
                    schema_column = SchemaColumnModel(
                        id=column_id,
                        table_id=schema_table.id,
                        name=column_data["name"],
                        type=column_data["type"],
                        constraints=column_data["constraints"]
                    )
                    db.add(schema_column)
                    column_id += 1

                table_id += 1

        # Фиксируем изменения после каждой таблицы схемы
        db.commit()
        print("Schema data created")

        # Добавляем мок-результаты для тестирования
        mock_results = {
    1: [
        {"id": 1, "name": "John Doe", "department_id": 1, "salary": 5000, "hire_date": "2020-01-15"},
        {"id": 2, "name": "Jane Smith", "department_id": 1, "salary": 6000, "hire_date": "2019-05-20"},
        {"id": 3, "name": "Bob Johnson", "department_id": 1, "salary": 4500, "hire_date": "2021-03-10"},
        {"id": 4, "name": "Alice Brown", "department_id": 1, "salary": 5500, "hire_date": "2018-11-01"},
        {"id": 5, "name": "Charlie Wilson", "department_id": 1, "salary": 4800, "hire_date": "2021-07-15"},
        {"id": 6, "name": "Dave Miller", "department_id": 2, "salary": 6500, "hire_date": "2017-09-20"},
        {"id": 7, "name": "Eve Davis", "department_id": 2, "salary": 5200, "hire_date": "2020-04-12"},
        {"id": 8, "name": "Frank White", "department_id": 2, "salary": 4900, "hire_date": "2021-01-25"},
        {"id": 9, "name": "Grace Taylor", "department_id": 3, "salary": 5300, "hire_date": "2019-08-05"},
        {"id": 10, "name": "Henry Martin", "department_id": 3, "salary": 6200, "hire_date": "2018-03-15"}
    ],
    2: [
        {"department_id": 1, "department_name": "Engineering", "count": 5},
        {"department_id": 2, "department_name": "Marketing", "count": 3},
        {"department_id": 3, "department_name": "HR", "count": 2},
        {"department_id": 4, "department_name": "Finance", "count": 0},
    ],
    3: [
        {"employee_name": "John Doe", "department_name": "Engineering", "project_count": 3},
        {"employee_name": "Jane Smith", "department_name": "Engineering", "project_count": 2},
        {"employee_name": "Bob Johnson", "department_name": "Engineering", "project_count": 1},
    ],
    4: [
        {"month": "2023-01", "product": "Laptop", "total_sales": 8400.00, "running_total": 8400.00},
        {"month": "2023-02", "product": "Laptop", "total_sales": 8400.00, "running_total": 16800.00},
        {"month": "2023-03", "product": "Laptop", "total_sales": 7200.00, "running_total": 24000.00},
    ],
    5: [
        {"employee_id": 1, "employee_name": "John Doe", "department_id": 1, "manager_employee_id": None},
        {"employee_id": 2, "employee_name": "Jane Smith", "department_id": 1, "manager_employee_id": 1},
        {"employee_id": 3, "employee_name": "Bob Johnson", "department_id": 1, "manager_employee_id": 2},
        {"employee_id": 4, "employee_name": "Alice Brown", "department_id": 1, "manager_employee_id": 1},
        {"employee_id": 5, "employee_name": "Charlie Wilson", "department_id": 1, "manager_employee_id": 3},
        {"employee_id": 6, "employee_name": "Dave Miller", "department_id": 2, "manager_employee_id": 1},
        {"employee_id": 7, "employee_name": "Eve Davis", "department_id": 2, "manager_employee_id": 2},
        {"employee_id": 8, "employee_name": "Frank White", "department_id": 2, "manager_employee_id": 3},
        {"employee_id": 9, "employee_name": "Grace Taylor", "department_id": 3, "manager_employee_id": 4},
        {"employee_id": 10, "employee_name": "Henry Martin", "department_id": 3, "manager_employee_id": 6}
    ]
}
        mock_id = 1

        for task_id, results in mock_results.items():
            mock_result = MockResultModel(
                id=mock_id,
                task_id=task_id,
                result_data=json.dumps(results)
            )
            db.add(mock_result)
            mock_id += 1

        db.commit()
        print("Mock results created")

                # Добавляем схемы результатов для каждой задачи
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
                {"name": "month", "type": "VARCHAR", "description": "Month of sales"},
                {"name": "product", "type": "VARCHAR", "description": "Product name"},
                {"name": "total_sales", "type": "DECIMAL", "description": "Total sales amount for the month"},
                {"name": "running_total", "type": "DECIMAL", "description": "Running total of sales"}
            ],
            5: [
                {"name": "employee_id", "type": "INTEGER", "description": "Employee ID"},
                {"name": "employee_name", "type": "VARCHAR", "description": "Employee name"},
                {"name": "department_id", "type": "INTEGER", "description": "Department ID"},
                {"name": "manager_employee_id", "type": "INTEGER", "description": "Manager's employee ID"}
            ]
        }

        schema_id = 1
        for task_id, schemas in result_schemas.items():
            for schema in schemas:
                result_schema = ResultSchemaModel(
                    id=schema_id,
                    task_id=task_id,
                    name=schema["name"],
                    type=schema["type"],
                    description=schema["description"]
                )
                db.add(result_schema)
                schema_id += 1

        db.commit()
        print("Result schemas created")

        # Создаем прогресс для админа
        admin = db.query(UserModel).filter(UserModel.username == "admin").first()
        if admin:
            progress_id = 1

            for task in db.query(TaskModel).all():
                progress = UserProgressModel(
                    id=progress_id,
                    user_id=admin.id,
                    task_id=task.id,
                    solved=False
                )
                db.add(progress)
                progress_id += 1

            db.commit()
            print("User progress initialized")

    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_data()
    print("Database initialization complete")

    print("\nCreating test tables for query validation...")
    create_test_tables()
    print("Test tables creation complete")
