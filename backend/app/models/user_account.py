from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountRole


class UserAccount(Base):
    """Cuenta interna de un empleado. La contraseña solo se guarda como hash bcrypt."""

    __tablename__ = "user_accounts"
    __table_args__ = (
        CheckConstraint(
            r"password_hash ~ '^\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}$'",
            name="ck_password_is_hash",
        ),
        CheckConstraint(
            "username = lower(username) AND username ~ '^[a-z][a-z0-9._]{2,59}$'",
            name="ck_username_normalized",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id"),
        unique=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AccountRole] = mapped_column(
        Enum(AccountRole, name="account_role"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    operator: Mapped["Operator"] = relationship(back_populates="account")
