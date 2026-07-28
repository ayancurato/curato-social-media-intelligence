"""
Curato AI — User Model
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """Represents a team member who can trigger content generations."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="team_member")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    generation_sessions = relationship("GenerationSession", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
