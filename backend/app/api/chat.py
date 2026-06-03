from fastapi import APIRouter, Depends, HTTPException

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

from backend.app.db.models import ChatMessage
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

    return messages

from backend.app.services.rag_engine import (
    retrieve_context
)

from backend.app.services.llm_service import (
    generate_answer
)

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
    content=answer
    )

    db.add(assistant_message)
    db.commit()

    return {
        "question": question,
        "answer": answer,
        "sources": chunk_ids
    }