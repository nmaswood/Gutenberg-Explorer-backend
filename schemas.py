from pydantic import BaseModel
from typing import Dict, Any , List , Optional

class BookSchema(BaseModel):
    id: str
    # content: str
    book_metadata: Dict[str, Any]  # Changed from str to Dict[str, Any] to handle JSON

    class Config:
        from_attributes = True  # Allows compatibility with SQLAlchemy models



