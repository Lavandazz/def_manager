from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Date, ForeignKey, Integer, Text, TIMESTAMP, func, BigInteger


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(Text)
    username: Mapped[str] = mapped_column(Text)
    telephone: Mapped[str] = mapped_column(Text, nullable=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    
    # связь с ролями через таблицу user_roles
    user_role: Mapped[Optional["UserRole"]] = relationship(back_populates="user")

    def __repr__(self) -> str: # вывод в консоль для отладки
        return f"User(id={self.id!r}, name={self.username!r}, fullname={self.email!r})"
    
    def __str__(self) -> str: # строковое представление для удобства чтения (логгер)
            return f"Пользователь {self.id}, username {self.username}"
    



class Role(Base):
    """
    Модель роли (Админ, Пользователь)
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(Text, unique=True)  # "admin", "user"

    # связь с пользователями через таблицу user_roles
    # list используется, так как одна роль может быть у нескольких пользователей
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")


class UserRole(Base):
    """
    Связь пользователя и роли
    """
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)  # Один пользователь может иметь только одну роль
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
 
    # user_role - связь с пользователем, back_populates указывает на атрибут в модели User, который ссылается на эту модель
    # role - связь с ролью, back_populates указывает на атрибут в модели Role, который ссылается на эту модель
    user: Mapped[User] = relationship(back_populates="user_role")
    role: Mapped["Role"] = relationship(back_populates="user_roles")  


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    number_case: Mapped[str] = mapped_column(Text, nullable=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    debtor: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=True, default=0)


class ParsDocument(Base):
    __tablename__ = "pars_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_case: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=True)
    date: Mapped[str] = mapped_column(Text, nullable=True)
    declarer: Mapped[str] = mapped_column(Text, nullable=True)
    document: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=True, default="not_sent")


class CourtSession(Base):
    __tablename__ = "court_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_case: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=True)
    date_court: Mapped[date] = mapped_column(Date, nullable=True)
    time_court: Mapped[str] = mapped_column(Text, nullable=True)
    hall_court: Mapped[str] = mapped_column(Text, nullable=True)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)   # BIGINT
    username: Mapped[str] = mapped_column(Text, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True, server_default=func.now())
    admin_response: Mapped[str] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=True, default="pending")


class BlackListToken(Base):
    """
    Модель для сохранения токена в черный лист токенов
    для дальнейшей проверки валидности токенов при входе
    """
    __tablename__ = "black_list_token"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(Text, nullable=False)
