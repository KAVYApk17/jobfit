from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import Unauthorized
from app.core.security import decode_access_token
from app.db import get_db
from app.repositories import UserRepo

_bearer = HTTPBearer(auto_error=False)

Db = Annotated[Session, Depends(get_db)]


def current_user_id(
    db: Db, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> UUID:
    """The user id always comes from the token, never from the request body."""
    if creds is None:
        raise Unauthorized("Missing bearer token.")
    user_id = decode_access_token(creds.credentials)
    if not UserRepo(db).exists(user_id):
        raise Unauthorized("This account no longer exists.")
    return user_id


CurrentUser = Annotated[UUID, Depends(current_user_id)]
