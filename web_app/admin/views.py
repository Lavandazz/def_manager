from sqladmin import ModelView
from shared.config.db.models import Account, Case, Debtor, User

class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    
    column_list = [User.id, User.email]


class CaseAdmin(ModelView, model=Case):
    name = "Дело"
    name_plural = "Дела"
    icon = "fa-solid fa-briefcase"

    # что показывать в списке
    column_list = [
        Case.id,
        Case.number_case,
        Case.date_case,
        Case.status,
        Case.debtor_name,
        Case.id_user,
        Case.debtor_id,
    ]

    # по каким колонкам искать
    # column_searchable_list = [Case.number_case, Case.debtor_name]

    # сортировка
    # column_sortable_list = [Case.id, Case.date_case, Case.status]
    column_default_sort = [(Case.id, True)]  # True = по убыванию

    # поля в форме создания/редактирования
    # ВАЖНО: relationship-поля (debtor, user, pars_documents, court_sessions)
    # НЕ включаем в form_columns — иначе sqladmin попытается их редактировать.
    # Вместо них используем скалярные FK: id_user и debtor_id.
    form_columns = [
        Case.number_case,
        Case.date_case,
        Case.status,
        Case.debtor_name,
        Case.link,
        Case.id_user,
        Case.debtor_id,
    ]

    # фильтры в сайдбаре
    # column_filters = [Case.status, Case.date_case]

    # отображение enum/int
    column_labels = {
        Case.number_case: "Номер дела",
        Case.debtor_name: "Должник",
        Case.date_case: "Дата дела",
        Case.status: "Статус",
        Case.link: "Ссылка",
        Case.id_user: "ID пользователя",
        Case.debtor_id: "ID должника",
    }

    # связь читаемым текстом вместо FK-числа
    # column_formatters = {
    #     Case.date_case: lambda m, a: m.date_case.strftime("%d.%m.%Y") if m.date_case else "",
    #     Case.debtor_id: lambda m, a: str(m.debtor) if m.debtor else "",
    # }


# ---------- Debtor ----------
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
    ]

    column_searchable_list = [Debtor.name, Debtor.inn, Debtor.snils]

    column_sortable_list = [Debtor.id, Debtor.name, Debtor.debtor_type]
    column_default_sort = [(Debtor.id, True)]

    # relationship-поля (accounts, birth_region, residential_address, cases)
    # в форму не включаем — только скалярные FK.
    form_columns = [
        Debtor.debtor_type,
        Debtor.name,
        Debtor.inn,
        Debtor.snils,
        Debtor.birthday,
        Debtor.birth_region_id,
        Debtor.residential_address_id,
    ]

    # column_filters = [Debtor.debtor_type, Debtor.birthday]

    column_labels = {
        Debtor.debtor_type: "Тип должника",
        Debtor.name: "Наименование / ФИО",
        Debtor.inn: "ИНН",
        Debtor.snils: "СНИЛС",
        Debtor.birthday: "Дата рождения",
        Debtor.birth_region_id: "Регион рождения",
        Debtor.residential_address_id: "Адрес прописки",
    }

    # Enum красиво отображается как "legal"/"physical"
    column_formatters = {
        Debtor.debtor_type: lambda m, a: m.debtor_type.value if m.debtor_type else "",
        Debtor.birthday: lambda m, a: m.birthday.strftime("%d.%m.%Y") if m.birthday else "",
    }


VIEWS = [UserAdmin, CaseAdmin, DebtorAdmin]
