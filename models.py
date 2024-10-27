from sqlalchemy import Column, String, Text, DateTime , JSON
from db_handler import Base
from sqlalchemy.sql import func

class Book(Base):
    __tablename__ = "books"
    
    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    book_metadata  = Column(JSON, nullable=False)
