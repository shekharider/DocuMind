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

from backend.app.db.models import (
    User,
    Document,
    ChatSession
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

    return {
        "id": document.id,
        "filename": document.filename,
        "session_id": document.session_id
    }