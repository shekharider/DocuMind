from fastapi import APIRouter
from fastapi import Depends

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