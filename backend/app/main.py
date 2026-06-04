from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.db.models import Base

from backend.app.api.auth import router as auth_router

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    columns = connection.execute(
        text("PRAGMA table_info(chat_messages)")
    ).fetchall()

    column_names = {
        column[1]
        for column in columns
    }

    if "sources" not in column_names:
        connection.execute(
            text(
                "ALTER TABLE chat_messages "
                "ADD COLUMN sources TEXT"
            )
        )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)


@app.get("/")
def root():
    return {
        "message": "DocuMind API Running"
    }

from backend.app.api.chat import router as chat_router

app.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"]
)

from backend.app.api.documents import (
    router as documents_router
)

app.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"]
)   
