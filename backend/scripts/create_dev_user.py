import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.clinical import User, UserRole


DEV_EMAIL = "psychologist@example.com"
DEV_PASSWORD = "devpassword123"


def main() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == DEV_EMAIL))
        if user is None:
            user = User(
                email=DEV_EMAIL,
                password_hash=hash_password(DEV_PASSWORD),
                role=UserRole.psychologist,
            )
            db.add(user)
            db.commit()
            print(f"Created dev user: {DEV_EMAIL}")
        else:
            print(f"Dev user already exists: {DEV_EMAIL}")

    print(f"Password: {DEV_PASSWORD}")


if __name__ == "__main__":
    main()
