from fastapi import FastAPI, Depends, HTTPException  , status , BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import requests
from typing import List , Generator
from schemas import BookSchema
from models import Book
from db_handler import get_db, engine, Base
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from analyzer import BookAnalyzer, ChatTogether
from data_cleaner import parse_gutenberg_rdf_metadata
from sqlalchemy.exc import SQLAlchemyError
import json
import os
from dotenv import load_dotenv


load_dotenv()

together_api_key = os.getenv("TOGETHER_API_KEY")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



chat = ChatTogether(
    together_api_key=str(together_api_key),
    model="meta-llama/Llama-3-70b-chat-hf",
)
analyzer = BookAnalyzer(chat)


# Create all tables
Base.metadata.create_all(bind=engine)




class BookRequest(BaseModel):
    book_id: str

@app.post("/books")
def fetch_and_save_book(book: BookRequest, db: Session = Depends(get_db)):
    book_id = book.book_id
    content_url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    rdf_metadata_url = f"https://www.gutenberg.org/ebooks/{book_id}.rdf"

    content_response = requests.get(content_url)
    if content_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Book content not found")

    # Fetch RDF metadata and parse it
    metadata_response = requests.get(rdf_metadata_url)
    if metadata_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Book metadata not found")
    
    metadata_html = metadata_response.content.decode('utf-8')
    book_content = content_response.text
    book_metadata = parse_gutenberg_rdf_metadata(metadata_html)


    new_book = Book(id=book_id, content=book_content, book_metadata=book_metadata)

    db.add(new_book)
    db.commit()
    return {"message": "Book saved successfully"}




@app.get("/books", response_model=List[BookSchema])
def get_books(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    # Convert books to dict and ensure book_metadata is parsed JSON
    return [
        {
            "id": book.id,
            "book_metadata": json.loads(book.book_metadata) if isinstance(book.book_metadata, str) else book.book_metadata
        }
        for book in books
    ]



@app.delete("/books", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book: BookRequest,  db: Session = Depends(get_db)):
    book_id = book.book_id
    # Find the book by id
    book = db.query(Book).filter(Book.id == str(book_id)).first()
    
    # If the book is not found, raise a 404 error
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Delete the book
    db.delete(book)
    db.commit()
    
    # No content is returned, as indicated by the 204 status code
    return



@app.get("/analyze-book/{book_id}")
def analyze_book_content(book_id: str, db: Session = Depends(get_db)):
    try:
        # Get book from database
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")

        # Create a generator for streaming analysis results
        def analyze_book_stream() -> Generator[str, None, None]:
            for analysis_chunk in analyzer.analyze_content(book.content):  # Call synchronous analyze_content
                yield analysis_chunk


        # Return the streaming response immediately
        return StreamingResponse(analyze_book_stream(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

