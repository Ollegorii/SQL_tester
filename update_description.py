# update_descriptions.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import task_descriptions
from db_init import TaskModel

# Настройки базы данных
DB_URL = "oracle+cx_oracle://USER_APP:maksim2003@158.160.94.135:1521/XE"

def update_task_descriptions():
    """Обновляет описания задач с добавлением информации о требуемых столбцах"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        for task_id, description in task_descriptions.items():
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.description = description
                print(f"Updated description for task {task_id}")
            else:
                print(f"Task {task_id} not found")
        
        session.commit()
        print("All task descriptions updated successfully")
    except Exception as e:
        session.rollback()
        print(f"Error updating task descriptions: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    update_task_descriptions()
