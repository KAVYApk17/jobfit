from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, Db
from app.services.auth import AuthService

router = APIRouter(prefix="/me", tags=["me"])


@router.delete("", status_code=204)
def delete_me(user_id: CurrentUser, db: Db) -> Response:
    """Delete the account; every table cascades from users, so this removes resumes, vectors and chats."""
    AuthService(db).delete_account(user_id)
    return Response(status_code=204)
