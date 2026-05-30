from fastapi import FastAPI

from backend.app.db.session import engine
from backend.app.db.models import Base

from backend.app.api.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

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