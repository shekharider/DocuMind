from fastapi import APIRouter, Depends, HTTPException
import json

from pathlib import Path


from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import ChatSession
from backend.app.db.chat_schemas import (
    ChatSessionCreate
)

from backend.app.api.auth import (
    get_current_user
)

from backend.app.db.models import User

router = APIRouter()


def parse_sources(sources):
    if not sources:
        return []

    try:
        return json.loads(sources)
    except json.JSONDecodeError:
        return []


def serialize_message(message):
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
        "session_id": message.session_id,
        "sources": parse_sources(message.sources)
    }

@router.post("/sessions")
def create_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    chat_session = ChatSession(
        title=session_data.title,
        user_id=current_user.id
    )

    db.add(chat_session)

    db.commit()

    db.refresh(chat_session)

    return {
        "id": chat_session.id,
        "title": chat_session.title
    }

@router.get("/sessions")
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).all()

    return sessions

@router.put("/sessions/{session_id}")
def update_session(
    session_id: int,
    session_data: ChatSessionCreate,
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

    session.title = session_data.title
    db.commit()
    db.refresh(session)

    return {
        "id": session.id,
        "title": session.title
    }

from backend.app.db.models import ChatMessage, Document, DocumentChunk
from backend.app.db.chat_schemas import MessageCreate


def get_conversation_history(
    session_id: int,
    db: Session,
    limit: int = 10
) -> str:
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(
        ChatMessage.created_at.desc()
    ).limit(limit).all()

    messages.reverse()

    if not messages:
        return ""

    formatted_lines = []
    for message in messages:
        role_label = "User" if message.role.lower() == "user" else "Assistant"
        formatted_lines.append(
            f"{role_label}: {message.content}"
        )

    return "\n\n".join(formatted_lines)


@router.post("/messages")
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    session = db.query(ChatSession).filter(
        ChatSession.id == message_data.session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    message = ChatMessage(
        session_id=message_data.session_id,
        role=message_data.role,
        content=message_data.content
    )

    db.add(message)

    db.commit()

    db.refresh(message)

    return {
        "id": message.id,
        "content": message.content
    }

@router.get("/messages/{session_id}")
def get_messages(
    session_id: int,
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

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).all()

    return [
        serialize_message(message)
        for message in messages
    ]

from backend.app.services.rag_engine import (
    retrieve_context,
    delete_session_embeddings,
)

from backend.app.services.llm_service import (
    generate_answer
)

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # 1) Delete Chroma vectors for the session
        delete_session_embeddings(session_id)

        # 2) Delete Messages
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete(synchronize_session=False)

        # 3) Delete Documents + Chunks
        documents = db.query(Document).filter(
            Document.session_id == session_id
        ).all()
        document_ids = [d.id for d in documents]

        if document_ids:
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id.in_(document_ids)
            ).delete(synchronize_session=False)

        if documents:
            for d in documents:
                db.delete(d)

        # 4) Delete the session row
        db.delete(session)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {e}")

    # 5) Delete filesystem folder recursively
    try:
        session_folder = Path(f"backend/data_storage/session_{session_id}")
        if session_folder.exists():
            # import locally to avoid unused imports
            import shutil
            shutil.rmtree(session_folder)
    except Exception:
        pass

    return {"message": "Session deleted successfully", "session_id": session_id}


@router.post("/ask")
def ask_question(

    session_id: int,
    question: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
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

    history = get_conversation_history(
        session_id,
        db,
        limit=10
    )

    user_message = ChatMessage(
    session_id=session_id,
    role="user",
    content=question
    )

    db.add(user_message)
    db.commit()

    retrieval = retrieve_context(
        question,
        session_id,
        db
    )

    context = retrieval["context"]

    chunk_ids = retrieval["chunk_ids"]

    answer = generate_answer(
        question,
        context,
        history
    )

    assistant_message = ChatMessage(
    session_id=session_id,
    role="assistant",
    content=answer,
    sources=json.dumps(chunk_ids)
    )

    db.add(assistant_message)
    db.commit()

    return {
        "question": question,
        "answer": answer,
        "sources": chunk_ids
    }
