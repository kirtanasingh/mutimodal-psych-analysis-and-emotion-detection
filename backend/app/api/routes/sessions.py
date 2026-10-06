from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.clinical import User
from app.schemas.session import SessionCreate, SessionOut
from app.services.session import create_session, get_owned_session, upload_video


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    return create_session(db, current_user.id, payload)


@router.get("/{session_id}", response_model=SessionOut)
def detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    return get_owned_session(db, current_user.id, session_id)


@router.post("/{session_id}/upload", response_model=SessionOut)
def upload(
    session_id: int,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    return upload_video(db, current_user.id, session_id, video)
