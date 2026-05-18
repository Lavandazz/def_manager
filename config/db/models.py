from datetime import date, datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Date, ForeignKey, Integer, Text, TIMESTAMP, func, BigInteger


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=True)
    # hashed_password: Mapped[str] = mapped_column(Text)
    username: Mapped[str] = mapped_column(Text)
    telephone: Mapped[str] = mapped_column(Text, nullable=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    

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
