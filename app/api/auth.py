from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.crud import user as user_crud
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    if user_crud.get_by_email(db, data.email) is not None:
        raise ConflictError("A user with this email already exists.", code="duplicate_email")
    user = user_crud.create_user(db, data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    """OAuth2 password flow: `username` is the user's email (lets Swagger's
    "Authorize" button drive this endpoint directly)."""
    user = user_crud.get_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password.", code="invalid_credentials")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)
