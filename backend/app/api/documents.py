from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi import HTTPException

from sqlalchemy.orm import Session

from pathlib import Path
import shutil

from backend.app.db.session import get_db

from backend.app.services.rag_engine import (
    extract_text_from_pdf,
    chunk_text,
    store_chunks_in_chroma
)

from backend.app.db.models import (
    User,
    Document,
    ChatSession,
    DocumentChunk
)

from backend.app.api.auth import (
    get_current_user
)

router = APIRouter()


@router.post("/upload")
def upload_document(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session_folder = Path(
        f"backend/data_storage/session_{session_id}"
    )

    session_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = session_folder / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    document = Document(
        filename=file.filename,
        filepath=str(file_path),
        session_id=session_id
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    text = extract_text_from_pdf(
        str(file_path)
    )

    chunks = chunk_text(text)

    saved_chunks = []

    for index, chunk in enumerate(chunks):

        db_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk
        )

        db.add(db_chunk)

        db.flush()

        saved_chunks.append(
            {
                "id": db_chunk.id,
                "content": chunk,
                "chunk_index": index
            }
        )

    db.commit()

    store_chunks_in_chroma(
        saved_chunks,
        document.id,
        session_id
    )

    return {
        "id": document.id,
        "filename": document.filename,
        "session_id": document.session_id,
        "chunks_created": len(saved_chunks)
    }


@router.get("/chunks/{document_id}")
def get_chunks(
    document_id: int,
    db: Session = Depends(get_db)
):
    return db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).limit(5).all()