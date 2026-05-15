from datetime import date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Date, ForeignKey, Integer, Text


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Text)
    telephone: Mapped[str] = mapped_column(Text)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    number_case: Mapped[str] = mapped_column(Text)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    debtor: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(Integer, default=0)


class ParsDocument(Base):
    __tablename__ = "pars_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_case: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    date: Mapped[str] = mapped_column(Text)
    declarer: Mapped[str] = mapped_column(Text)
    document: Mapped[str] = mapped_column(Text)


class CourtSession(Base):
    __tablename__ = "court_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_case: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    date_court: Mapped[date] = mapped_column(Date)
    time_court: Mapped[str] = mapped_column(Text)
    hall_court: Mapped[str] = mapped_column(Text)
