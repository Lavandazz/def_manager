from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from shared.config.db.models import (
    Account,
    Address,
    Bank,
    BlackListToken,
    Case,
    Court,
    CourtSession,
    Debtor,
    MailAddress,
    ParsDocument,
    Region,
    ResidentialAddress,
    Role,
    Sro,
    SupportTicket,
    User,
    UserRole,
)


def _loaded(instance, attribute):
    """Return relationship/collection only if SQLAlchemy already loaded it."""
    if instance is None:
        return None
    return instance.__dict__.get(attribute)


def format_region(region):
    if region is None:
        return ""
    region_name = _loaded(region, "region_name")
    city = _loaded(region, "city")
    parts = [region_name, city]
    return ", ".join(str(part) for part in parts if part)


def format_address(address):
    if address is None:
        return ""
    street = _loaded(address, "street")
    house = _loaded(address, "house")
    building = _loaded(address, "building")
    parts = [street, house]
    if building:
        parts.append(f"корп. {building}")
    return ", ".join(str(part) for part in parts if part)


def format_mail_address(mail_address):
    if mail_address is None:
        return ""
    mail_index = _loaded(mail_address, "mail_index")
    region = _loaded(mail_address, "region")
    address = _loaded(mail_address, "address")
    parts = [str(mail_index) if mail_index is not None else "", format_region(region), format_address(address)]
    return ", ".join(part for part in parts if part)


def format_residential_address(residential_address):
    if residential_address is None:
        return ""
    region = _loaded(residential_address, "region")
    address = _loaded(residential_address, "address")
    flat = _loaded(residential_address, "flat")
    parts = [format_region(region), format_address(address)]
    if flat:
        parts.append(f"кв. {flat}")
    return ", ".join(part for part in parts if part)


def format_user(user):
    if user is None:
        return ""
    username = _loaded(user, "username")
    email = _loaded(user, "email")
    user_id = _loaded(user, "id")
    return str(username or email or f"Пользователь #{user_id}")


def format_role(role):
    if role is None:
        return ""
    role_name = _loaded(role, "role")
    role_names = {"admin": "Администратор", "user": "Пользователь"}
    if role_name is None:
        return ""
    return role_names.get(str(role_name), str(role_name))


def format_debtor(debtor):
    if debtor is None:
        return ""
    return str(_loaded(debtor, "name") or "")


def format_bank(bank):
    if bank is None:
        return ""
    return str(_loaded(bank, "name") or "")


def format_case(case):
    if case is None:
        return ""
    number = _loaded(case, "number_case")
    date_case = _loaded(case, "date_case")
    date_text = date_case.strftime("%d.%m.%Y") if date_case else ""
    return f"{number or 'Дело'}{f' от {date_text}' if date_text else ''}"


def format_accounts(accounts):
    if not accounts:
        return ""
    numbers = []
    for account in accounts:
        number = _loaded(account, "number")
        if number:
            numbers.append(str(number))
    return ", ".join(numbers)


def format_cases(cases):
    if not cases:
        return ""
    return ", ".join(format_case(case) for case in cases)


def format_debtor_type(debtor_type):
    if debtor_type is None:
        return ""
    if getattr(debtor_type, "value", None) == "legal":
        return "Юридическое лицо"
    return "Физическое лицо"


def format_date(value):
    if value is None:
        return ""
    return value.strftime("%d.%m.%Y")


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.username,
        User.email,
        User.telephone,
        User.inn,
        User.reg_num,
        User.sro,
        User.mail_address,
    ]
    column_searchable_list = []
    column_sortable_list = [
        User.id,
        User.username,
        User.email,
        User.telephone,
        User.reg_num,
    ]
    column_default_sort = [(User.id, True)]

    form_columns = [
        User.email,
        User.username,
        User.telephone,
        User.telegram_id,
        User.inn,
        User.snils,
        User.reg_num,
        User.reg_date,
        User.date_begin,
        User.sro,
        User.mail_address,
    ]

    column_labels = {
        User.id: "ID",
        User.username: "Логин / имя",
        User.email: "Email",
        User.telephone: "Телефон",
        User.telegram_id: "Telegram ID",
        User.inn: "ИНН",
        User.snils: "СНИЛС",
        User.reg_num: "Рег. номер",
        User.reg_date: "Дата регистрации",
        User.date_begin: "Дата вступления",
        User.sro: "СРО",
        User.mail_address: "Почтовый адрес",
    }

    column_formatters = {
        User.mail_address: lambda m, a: format_mail_address(_loaded(m, "mail_address")),
        User.sro: lambda m, a: str(_loaded(m, "sro")) if _loaded(m, "sro") is not None else "",
        User.reg_date: lambda m, a: (
            m.reg_date.strftime("%d.%m.%Y") if _loaded(m, "reg_date") else ""
        ),
        User.date_begin: lambda m, a: (
            m.date_begin.strftime("%d.%m.%Y") if _loaded(m, "date_begin") else ""
        ),
    }


class CaseAdmin(ModelView, model=Case):
    name = "Дело"
    name_plural = "Дела"
    icon = "fa-solid fa-briefcase"

    column_list = [
        Case.id,
        Case.number_case,
        Case.date_case,
        Case.status,
        Case.debtor_name,
        Case.user,
        Case.debtor,
        Case.link,
    ]
    column_searchable_list = []
    column_sortable_list = [Case.id, Case.number_case, Case.date_case, Case.status]
    column_default_sort = [(Case.id, True)]

    form_columns = [
        Case.number_case,
        Case.date_case,
        Case.status,
        Case.debtor_name,
        Case.link,
        Case.user,
        Case.debtor,
    ]

    column_labels = {
        Case.id: "ID",
        Case.number_case: "Номер дела",
        Case.debtor_name: "Должник (текст)",
        Case.date_case: "Дата дела",
        Case.status: "Статус",
        Case.link: "Ссылка",
        Case.user: "Пользователь",
        Case.debtor: "Должник",
    }

    column_formatters = {
        Case.date_case: lambda m, a: (
            m.date_case.strftime("%d.%m.%Y") if m.date_case else ""
        ),
        Case.user: lambda m, a: format_user(m.user),
        Case.debtor: lambda m, a: format_debtor(m.debtor),
    }


class DebtorAdmin(ModelView, model=Debtor):
    name = "Должник"
    name_plural = "Должники"
    icon = "fa-solid fa-users"

    column_list = [
        Debtor.id,
        Debtor.debtor_type,
        Debtor.name,
        Debtor.inn,
        Debtor.snils,
        Debtor.birthday,
        Debtor.birth_region,
        Debtor.residential_address,
        Debtor.accounts,
        Debtor.cases,
    ]

    column_searchable_list = [Debtor.name, Debtor.inn, Debtor.snils]
    column_sortable_list = [Debtor.id, Debtor.name, Debtor.debtor_type, Debtor.birthday]
    column_default_sort = [(Debtor.id, True)]

    form_columns = [
        Debtor.debtor_type,
        Debtor.name,
        Debtor.inn,
        Debtor.snils,
        Debtor.birthday,
        Debtor.birth_region,
        Debtor.residential_address,
    ]

    column_labels = {
        Debtor.id: "ID",
        Debtor.debtor_type: "Тип должника",
        Debtor.name: "Наименование / ФИО",
        Debtor.inn: "ИНН",
        Debtor.snils: "СНИЛС",
        Debtor.birthday: "Дата рождения",
        Debtor.birth_region: "Регион рождения",
        Debtor.residential_address: "Адрес прописки",
        Debtor.accounts: "Счета",
        Debtor.cases: "Дела",
    }

    column_formatters = {
        Debtor.debtor_type: lambda m, a: format_debtor_type(
            _loaded(m, "debtor_type")
        ),
        Debtor.birthday: lambda m, a: format_date(_loaded(m, "birthday")),
        Debtor.birth_region: lambda m, a: format_region(_loaded(m, "birth_region")),
        Debtor.residential_address: lambda m, a: format_residential_address(
            _loaded(m, "residential_address")
        ),
        Debtor.accounts: lambda m, a: format_accounts(_loaded(m, "accounts") or []),
        Debtor.cases: lambda m, a: format_cases(_loaded(m, "cases") or []),
    }


class AccountAdmin(ModelView, model=Account):
    name = "Счёт"
    name_plural = "Счета"
    icon = "fa-solid fa-wallet"

    column_list = [Account.id, Account.number, Account.debtor, Account.bank]
    column_searchable_list = [Account.number]
    column_sortable_list = [Account.id, Account.number]
    form_columns = [Account.number, Account.debtor, Account.bank]

    column_labels = {
        Account.id: "ID",
        Account.number: "Номер счёта",
        Account.debtor: "Должник",
        Account.bank: "Банк",
    }

    column_formatters = {
        Account.debtor: lambda m, a: format_debtor(m.debtor),
        Account.bank: lambda m, a: format_bank(m.bank),
    }


class BankAdmin(ModelView, model=Bank):
    name = "Банк"
    name_plural = "Банки"
    icon = "fa-solid fa-building-columns"

    column_list = [Bank.id, Bank.name, Bank.mail_address]
    column_searchable_list = [Bank.name]
    column_sortable_list = [Bank.id, Bank.name]
    form_columns = [Bank.name, Bank.mail_address]

    column_labels = {
        Bank.id: "ID",
        Bank.name: "Наименование банка",
        Bank.mail_address: "Почтовый адрес",
    }

    column_formatters = {
        Bank.mail_address: lambda m, a: format_mail_address(_loaded(m, "mail_address")),
    }

class SroAdmin(ModelView, model=Sro):
    name = "СРО"
    name_plural = "СРО"
    icon = "fa-solid fa-landmark"

    column_list = [Sro.id, Sro.name, Sro.reg_num, Sro.inn, Sro.phone, Sro.email]
    column_searchable_list = [Sro.name, Sro.reg_num, Sro.inn, Sro.email]
    column_sortable_list = [Sro.id, Sro.name, Sro.reg_num, Sro.inn]
    form_columns = [
        Sro.name,
        Sro.reg_num,
        Sro.reg_date,
        Sro.inn,
        Sro.ogrn,
        Sro.ur_address_sro,
        Sro.phone,
        Sro.email,
        Sro.url,
    ]

    column_labels = {
        Sro.id: "ID",
        Sro.name: "Наименование",
        Sro.reg_num: "Регистрационный номер",
        Sro.reg_date: "Дата регистрации",
        Sro.inn: "ИНН",
        Sro.ogrn: "ОГРН",
        Sro.ur_address_sro: "Юридический адрес",
        Sro.phone: "Телефон",
        Sro.email: "Email",
        Sro.url: "Сайт",
    }

    column_formatters = {
        Sro.reg_date: lambda m, a: (
            m.reg_date.strftime("%d.%m.%Y") if m.reg_date else ""
        ),
    }


class RoleAdmin(ModelView, model=Role):
    name = "Роль"
    name_plural = "Роли"
    icon = "fa-solid fa-shield-halved"

    column_list = [Role.id, Role.role]
    column_searchable_list = [Role.role]
    column_sortable_list = [Role.id, Role.role]
    form_columns = [Role.role]

    column_labels = {
        Role.id: "ID",
        Role.role: "Наименование роли",
    }

    column_formatters = {
        Role.role: lambda m, a: format_role(m),
    }


class UserRoleAdmin(ModelView, model=UserRole):
    name = "Роль пользователя"
    name_plural = "Роли пользователей"
    icon = "fa-solid fa-user-tag"

    column_list = [UserRole.id, UserRole.user, UserRole.role]
    column_searchable_list = [UserRole.user, UserRole.role]
    column_sortable_list = [UserRole.id]
    form_columns = [UserRole.user, UserRole.role]

    column_labels = {
        UserRole.id: "ID",
        UserRole.user: "Пользователь",
        UserRole.role: "Роль",
    }

    column_formatters = {
        UserRole.user: lambda m, a: format_user(m.user),
        UserRole.role: lambda m, a: format_role(m.role),
    }


class CourtAdmin(ModelView, model=Court):
    name = "Суд"
    name_plural = "Суды"
    icon = "fa-solid fa-gavel"

    column_list = [Court.id, Court.name]
    column_searchable_list = [Court.name]
    column_sortable_list = [Court.id, Court.name]
    form_columns = [Court.name]

    column_labels = {
        Court.id: "ID",
        Court.name: "Наименование суда",
    }


class CourtSessionAdmin(ModelView, model=CourtSession):
    name = "Судебное заседание"
    name_plural = "Судебные заседания"
    icon = "fa-solid fa-calendar-check"

    column_list = [
        CourtSession.id,
        CourtSession.case,
        CourtSession.date_court,
        CourtSession.time_court,
        CourtSession.hall_court,
        CourtSession.court,
    ]
    column_searchable_list = [CourtSession.hall_court, CourtSession.time_court]
    column_sortable_list = [
        CourtSession.id,
        CourtSession.date_court,
    ]
    form_columns = [
        CourtSession.case,
        CourtSession.date_court,
        CourtSession.time_court,
        CourtSession.hall_court,
        CourtSession.court,
    ]

    column_labels = {
        CourtSession.id: "ID",
        CourtSession.case: "Дело",
        CourtSession.date_court: "Дата заседания",
        CourtSession.time_court: "Время",
        CourtSession.hall_court: "Зал",
        CourtSession.court: "Суд",
    }

    column_formatters = {
        CourtSession.date_court: lambda m, a: (
            m.date_court.strftime("%d.%m.%Y") if m.date_court else ""
        ),
        CourtSession.case: lambda m, a: format_case(m.case),
        CourtSession.court: lambda m, a: str(m.court.name) if m.court else "",
    }


class ParsDocumentAdmin(ModelView, model=ParsDocument):
    name = "Документ"
    name_plural = "Документы"
    icon = "fa-solid fa-file-lines"

    column_list = [
        ParsDocument.id,
        ParsDocument.case,
        ParsDocument.date,
        ParsDocument.declarer,
        ParsDocument.status,
    ]
    column_searchable_list = [ParsDocument.declarer, ParsDocument.status]
    column_sortable_list = [ParsDocument.id, ParsDocument.date]
    form_columns = [
        ParsDocument.case,
        ParsDocument.date,
        ParsDocument.declarer,
        ParsDocument.document,
        ParsDocument.status,
    ]

    column_labels = {
        ParsDocument.id: "ID",
        ParsDocument.case: "Дело",
        ParsDocument.date: "Дата",
        ParsDocument.declarer: "Заявитель",
        ParsDocument.document: "Документ",
        ParsDocument.status: "Статус",
    }

    column_formatters = {
        ParsDocument.date: lambda m, a: m.date.strftime("%d.%m.%Y") if m.date else "",
        ParsDocument.case: lambda m, a: format_case(m.case),
    }


class SupportTicketAdmin(ModelView, model=SupportTicket):
    name = "Тикет поддержки"
    name_plural = "Тикеты поддержки"
    icon = "fa-solid fa-ticket"

    column_list = [
        SupportTicket.id,
        SupportTicket.user_id,
        SupportTicket.username,
        SupportTicket.status,
        SupportTicket.created_at,
    ]
    column_searchable_list = [
        SupportTicket.username,
        SupportTicket.status,
        SupportTicket.message,
    ]
    column_sortable_list = [
        SupportTicket.id,
        SupportTicket.user_id,
        SupportTicket.created_at,
        SupportTicket.status,
    ]
    form_columns = [
        SupportTicket.user_id,
        SupportTicket.username,
        SupportTicket.message,
        SupportTicket.status,
        SupportTicket.admin_response,
        SupportTicket.responded_at,
    ]

    column_labels = {
        SupportTicket.id: "ID",
        SupportTicket.user_id: "Пользователь",
        SupportTicket.username: "Имя пользователя",
        SupportTicket.message: "Сообщение",
        SupportTicket.created_at: "Создано",
        SupportTicket.admin_response: "Ответ администратора",
        SupportTicket.responded_at: "Дата ответа",
        SupportTicket.status: "Статус",
    }

    column_formatters = {
        SupportTicket.created_at: lambda m, a: (
            m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else ""
        ),
        SupportTicket.responded_at: lambda m, a: (
            m.responded_at.strftime("%d.%m.%Y %H:%M") if m.responded_at else ""
        ),
    }


class BlackListTokenAdmin(ModelView, model=BlackListToken):
    name = "Черный список токенов"
    name_plural = "Черные списки токенов"
    icon = "fa-solid fa-ban"

    column_list = [BlackListToken.id, BlackListToken.token]
    column_searchable_list = [BlackListToken.token]
    column_sortable_list = [BlackListToken.id]
    form_columns = [BlackListToken.token]

    column_labels = {
        BlackListToken.id: "ID",
        BlackListToken.token: "Токен",
    }


class RegionAdmin(ModelView, model=Region):
    name = "Регион"
    name_plural = "Регионы"
    icon = "fa-solid fa-map-location-dot"

    column_list = [Region.id, Region.region_name, Region.city]
    column_searchable_list = [Region.region_name, Region.city]
    column_sortable_list = [Region.id, Region.region_name, Region.city]
    form_columns = [Region.region_name, Region.city]

    column_labels = {
        Region.id: "ID",
        Region.region_name: "Регион",
        Region.city: "Город",
    }


class AddressAdmin(ModelView, model=Address):
    name = "Адрес"
    name_plural = "Адреса"
    icon = "fa-solid fa-location-dot"

    column_list = [Address.id, Address.street, Address.house, Address.building]
    column_searchable_list = [Address.street, Address.house]
    column_sortable_list = [Address.id, Address.street, Address.house]
    form_columns = [Address.street, Address.house, Address.building]

    column_labels = {
        Address.id: "ID",
        Address.street: "Улица",
        Address.house: "Дом",
        Address.building: "Корпус",
    }


class MailAddressAdmin(ModelView, model=MailAddress):
    name = "Почтовый адрес"
    name_plural = "Почтовые адреса"
    icon = "fa-solid fa-envelope"

    column_list = [
        MailAddress.id,
        MailAddress.mail_index,
        MailAddress.region,
        MailAddress.address,
    ]
    column_searchable_list = [MailAddress.mail_index]
    column_sortable_list = [MailAddress.id, MailAddress.mail_index]
    form_columns = [
        MailAddress.mail_index,
        MailAddress.region,
        MailAddress.address,
    ]

    column_labels = {
        MailAddress.id: "ID",
        MailAddress.mail_index: "Почтовый индекс",
        MailAddress.region: "Регион",
        MailAddress.address: "Адрес",
    }

    column_formatters = {
        MailAddress.region: lambda m, a: format_region(_loaded(m, "region")),
        MailAddress.address: lambda m, a: format_address(_loaded(m, "address")),
    }



class ResidentialAddressAdmin(ModelView, model=ResidentialAddress):
    name = "Адрес прописки"
    name_plural = "Адреса прописки"
    icon = "fa-solid fa-house-user"

    column_list = [
        ResidentialAddress.id,
        ResidentialAddress.region,
        ResidentialAddress.address,
        ResidentialAddress.flat,
    ]
    column_searchable_list = [ResidentialAddress.flat]
    column_sortable_list = [ResidentialAddress.id, ResidentialAddress.flat]
    form_columns = [
        ResidentialAddress.region,
        ResidentialAddress.address,
        ResidentialAddress.flat,
    ]

    column_labels = {
        ResidentialAddress.id: "ID",
        ResidentialAddress.region: "Регион",
        ResidentialAddress.address: "Адрес",
        ResidentialAddress.flat: "Квартира",
    }

    column_formatters = {
        ResidentialAddress.region: lambda m, a: format_region(_loaded(m, "region")),
        ResidentialAddress.address: lambda m, a: format_address(_loaded(m, "address")),
    }


VIEWS = [
    UserAdmin,
    CaseAdmin,
    DebtorAdmin,
    AccountAdmin,
    BankAdmin,
    SroAdmin,
    RoleAdmin,
    UserRoleAdmin,
    CourtAdmin,
    CourtSessionAdmin,
    ParsDocumentAdmin,
    SupportTicketAdmin,
    BlackListTokenAdmin,
    RegionAdmin,
    AddressAdmin,
    MailAddressAdmin,
    ResidentialAddressAdmin,
]
