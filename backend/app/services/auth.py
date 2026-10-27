from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import EmailTaken, Unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories import UserRepo


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepo(db)

    def register(self, email: str, password: str) -> User:
        email = email.strip().lower()
        if self.users.get_by_email(email):
            raise EmailTaken("An account with this email already exists.")
        try:
            user = self.users.create(email, hash_password(password))
            self.db.commit()
        except IntegrityError:  # two registrations racing for the same email
            self.db.rollback()
            raise EmailTaken("An account with this email already exists.")
        return user

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or not verify_password(user.password_hash, password):
            raise Unauthorized("Invalid email or password.")
        return create_access_token(user.id)

    def delete_account(self, user_id: UUID) -> None:
        self.users.delete(user_id)
        self.db.commit()
