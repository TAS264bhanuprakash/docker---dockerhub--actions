from database import engine, Base
import models

# Create all tables
Base.metadata.create_all(bind=engine)
