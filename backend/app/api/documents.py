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
    store_chunks_in_chroma,
    delete_document_embeddings,
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


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify document belongs to current authenticated user via its session
    session = db.query(ChatSession).filter(
        ChatSession.id == document.session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Document not found")

    # Determine chunk ids for Chroma deletion
    chunk_ids = [
        c.id for c in db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    ]

    try:
        # Delete embeddings from Chroma for this document
        delete_document_embeddings(document_id)

        # Delete chunks from SQL
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete(synchronize_session=False)

        # Delete the document row
        db.delete(document)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")

    # Delete PDF from filesystem (outside transaction)
    try:
        pdf_path = Path(document.filepath)
        if pdf_path.exists():
            pdf_path.unlink()

        # If the session folder becomes empty, remove it
        session_folder = Path(f"backend/data_storage/session_{document.session_id}")
        if session_folder.exists() and next(session_folder.iterdir(), None) is None:
            session_folder.rmdir()
    except Exception:
        # If FS deletion fails, keep the DB consistent but notify client
        # (could be logged in real deployments)
        pass

    return {"message": "Document deleted successfully", "document_id": document_id}


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
        session_id,
        document.filename
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    session = db.query(ChatSession).filter(
        ChatSession.id == document.session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).limit(5).all()


@router.get("/session/{session_id}")
def get_session_documents(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    session = db.query(
        ChatSession
    ).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    documents = db.query(
        Document
    ).filter(
        Document.session_id == session_id
    ).all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename
        }
        for doc in documents
    ]

 