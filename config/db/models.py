import enum
from datetime import date, datetime

from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Date, ForeignKey, Integer, Text, TIMESTAMP, func, BigInteger, Enum as SQLEnum, String
from traitlets import Int


class Base(DeclarativeBase):
    pass

class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    number_case: Mapped[str] = mapped_column(Text, nullable=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    debtor_name: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    debtor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("debtors.id"), nullable=True)  # поле для связи с таблицей Debtor
    
    debtor: Mapped[Optional["Debtor"]] = relationship(back_populates="cases")
    # связь c документами, back_populates указывает на атрибут в модели ParsDocument, который ссылается на эту модель
    pars_documents = relationship("ParsDocument", back_populates="case")
    court_sessions = relationship("CourtSession", back_populates="case")
    user = relationship("User", back_populates="cases", foreign_keys=[id_user])


class DebtorType(enum.Enum):
    """
    Тип должника (юр лицо или физ лицо)
    """
    LEGAL = "legal"
    PHYSICAL = "physical"


class Debtor(Base):
    __tablename__ = "debtors"
    id: Mapped[int] = mapped_column(primary_key=True)
    debtor_type: Mapped[DebtorType] = mapped_column(SQLEnum(DebtorType), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    inn: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # для юрлиц обязателен, для физлиц опционален
    snils: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # только для физлиц
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True)   # только для физлиц

    accounts: Mapped[list["Account"]] = relationship(back_populates="debtor")

    # Связь места рождения — только для физлиц, ссылка на регион
    birth_region_id: Mapped[int | None] = mapped_column(ForeignKey("region.id", ondelete="RESTRICT", name="fk_debtors_birth_region"), nullable=True)
    birth_region: Mapped["Region | None"] = relationship()

    # Связь места прописки. нельзя удалить адрес/банк, пока на него кто-то ссылается
    residential_address_id: Mapped[int | None] = mapped_column(ForeignKey("residential_address.id", ondelete="RESTRICT", name="fk_debtors_residential_address"), nullable=True)

    # Обратная связь с делами
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="debtor")


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
    cases = relationship("Case", back_populates="user", foreign_keys=[Case.id_user])

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


class ParsDocument(Base):
    __tablename__ = "pars_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_case: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=True)
    declarer: Mapped[str] = mapped_column(Text, nullable=True)
    document: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=True, default="not_sent")

    case = relationship("Case", back_populates="pars_documents")


class Court(Base):
    __tablename__ = "courts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=True, unique=True)
    court_sessions = relationship("CourtSession", back_populates="court")


class CourtSession(Base):
    __tablename__ = "court_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_case: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=True)
    date_court: Mapped[date] = mapped_column(Date, nullable=True)
    time_court: Mapped[str] = mapped_column(Text, nullable=True)
    hall_court: Mapped[str] = mapped_column(Text, nullable=True)

    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), nullable=True)

    case = relationship("Case", back_populates="court_sessions")
    court = relationship("Court", back_populates="court_sessions")


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


class Region(Base):
    """
    Таблица регион используется в почтовом адресе и адресе регистрации должника.
    Так как регион не всегда указывается, то может быть пустым. Но город указывается обязательно
    """
    __tablename__= "region"
    id: Mapped[int] = mapped_column(primary_key=True)
    region_name: Mapped[str] = mapped_column(Text, nullable=True, default=None)
    city: Mapped[str] = mapped_column(Text, nullable=False)

class Address(Base):
    """
    Таблица адреса используется в почтовом, адресе регистрации должника. Указывается только улица, дом, строение
    """
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    street: Mapped[str] = mapped_column(Text, nullable=False)
    house: Mapped[str] = mapped_column(Text, nullable=False)
    building: Mapped[str] = mapped_column(Text, nullable=True, default=None)

class MailAddress(Base):
    """Почтовый адрес используется для указания адреса Банка.
    Связь с банком
    """
    __tablename__ = "mail_address"
    id: Mapped[int] = mapped_column(primary_key=True)
    mail_index: Mapped[int] = mapped_column(Integer, nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("region.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("address.id"), nullable=False)

    region: Mapped["Region"] = relationship()
    address: Mapped["Address"] = relationship()


class ResidentialAddress(Base):
    """Адрес прописки используется для указания адреса прописки должника. 
    Связь с должником
    """
    __tablename__ = "residential_address"
    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("region.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("address.id"), nullable=False)
    flat: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    region: Mapped["Region"] = relationship()
    address: Mapped["Address"] = relationship()


class Bank(Base):
    """
    Данные для счетов должника в банке.
    Связь со счетами и должником. 
    У одного должника может быть несколько банков, у одного банка несколько счетов и несколько должников.
    """
    __tablename__ = "bank"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # Запрещает удалить адрес, если он используется
    mail_address_id: Mapped[int] = mapped_column(ForeignKey("mail_address.id", ondelete="RESTRICT"), nullable=False)
    mail_address: Mapped["MailAddress"] = relationship(cascade="all, delete-orphan",single_parent=True,) # 
    accounts: Mapped[list["Account"]] = relationship(back_populates="bank")


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(Text, nullable=False)  # № счёта, храни строкой

    debtor_id: Mapped[int] = mapped_column(ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id", ondelete="RESTRICT"), nullable=False)

    debtor: Mapped["Debtor"] = relationship(back_populates="accounts")
    bank: Mapped["Bank"] = relationship(back_populates="accounts")

    def __repr__(self) -> str:
        return f"Account(id={self.id!r}, number={self.number!r})"