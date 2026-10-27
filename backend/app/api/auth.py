from fastapi import APIRouter

from app.api.deps import Db
from app.config import get_settings
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserOut)
def register(body: RegisterIn, db: Db) -> UserOut:
    user = AuthService(db).register(body.email, body.password)
    return UserOut(id=user.id, email=user.email)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Db) -> TokenOut:
    token = AuthService(db).login(body.email, body.password)
    return TokenOut(access_token=token, expires_in=get_settings().jwt_ttl_minutes * 60)
