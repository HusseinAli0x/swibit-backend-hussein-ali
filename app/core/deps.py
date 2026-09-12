from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.models.user import User

# tokenUrl is only used to populate Swagger's "Authorize" flow; the actual
# route lives under the /auth router.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if token is None:
        raise UnauthorizedError("Missing or malformed Authorization header.")
    subject = decode_access_token(token)
    if subject is None:
        raise UnauthorizedError("Invalid or expired access token.")
    user = user_crud.get_by_id(db, int(subject))
    if user is None:
        raise UnauthorizedError("User for this token no longer exists.")
    return user
