from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse
from app.services.auth import authenticate_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    authenticated = authenticate_user(db, payload.email, payload.password)
    if authenticated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, access_token = authenticated
    return TokenResponse(access_token=access_token, user=user)


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response) -> LogoutResponse:
    response.delete_cookie("access_token")
    return LogoutResponse(message="Logged out")
