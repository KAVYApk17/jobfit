from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.flush()
        return user

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def exists(self, user_id: UUID) -> bool:
        return self.db.scalar(select(User.id).where(User.id == user_id)) is not None

    def delete(self, user_id: UUID) -> None:
        # ON DELETE CASCADE removes resumes, jobs, chunks, tasks and everything added later.
        self.db.execute(delete(User).where(User.id == user_id))
