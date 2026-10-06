from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.clinical import User


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, str] | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user, create_access_token(str(user.id))
