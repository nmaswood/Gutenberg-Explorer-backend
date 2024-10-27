from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os


load_dotenv()

# Fetch database credentials from environment variables
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")  # Default to localhost
DB_PORT = os.getenv("POSTGRES_PORT", "5432")       # Default to 5432
DB_NAME = os.getenv("POSTGRES_DB")



# Database URL should ideally be stored in environment variables for security.
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a global engine that will be used across the app
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class and bind it to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base for models
Base = declarative_base()

# get a DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close() 
