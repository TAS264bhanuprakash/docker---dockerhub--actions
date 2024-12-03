# init_db.py
from database import engine
import models

def init_database():
    models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")