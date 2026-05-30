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