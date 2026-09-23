
from datetime import date, datetime

def to_int_or_none(v: str) -> int | None:
    v = (v or "").strip()
    return int(v) if v else None

def to_date_or_none(v: str) -> date | None:
    v = (v or "").strip()
    return datetime.strptime(v, "%Y-%m-%d").date() if v else None



def _parse_accounts_from_form(form) -> tuple[list[dict], list[str]]:
    """
    Собирает строки счетов из form.getlist().
    Параллельные массивы связаны по индексу.
    bank_id == '__new__' → создаём банк с почтовым адресом.
    """
    ids         = form.getlist("account_id[]")
    numbers     = form.getlist("account_number[]")
    bank_ids    = form.getlist("account_bank_id[]")
    new_names   = form.getlist("new_bank_name[]")
    new_indices = form.getlist("new_bank_mail_index[]")
    new_regions = form.getlist("new_bank_region_name[]")
    new_cities  = form.getlist("new_bank_city[]")
    new_streets = form.getlist("new_bank_street[]")
    new_houses  = form.getlist("new_bank_house[]")
    new_bldgs   = form.getlist("new_bank_building[]")

    row_count = max(
        len(ids), len(numbers), len(bank_ids),
        len(new_names), len(new_cities),
    )
    accounts: list[dict] = []
    errors: list[str] = []

    for i in range(row_count):
        raw_id   = (ids[i] if i < len(ids) else "").strip()
        number   = (numbers[i] if i < len(numbers) else "").strip()
        bank_raw = (bank_ids[i] if i < len(bank_ids) else "").strip()

        # полностью пустая строка — пропускаем
        if not number and not bank_raw:
            continue

        item: dict = {
            "id": int(raw_id) if raw_id else None,
            "number": number or None,
        }

        if bank_raw == "__new__":
            name   = (new_names[i] if i < len(new_names) else "").strip()
            city   = (new_cities[i] if i < len(new_cities) else "").strip()
            street = (new_streets[i] if i < len(new_streets) else "").strip()
            house  = (new_houses[i] if i < len(new_houses) else "").strip()

            if not name:
                errors.append(f"Счёт #{i + 1}: укажите название нового банка")
                continue
            if not (city and street and house):
                errors.append(
                    f"Счёт #{i + 1}: для банка «{name}» нужны город, улица и дом"
                )
                continue

            item["bank_name"] = name
            item["bank_mail_index"] = to_int_or_none(
                new_indices[i] if i < len(new_indices) else ""
            )
            item["bank_region_name"] = (
                (new_regions[i] if i < len(new_regions) else "").strip() or None
            )
            item["bank_city"] = city
            item["bank_street"] = street
            item["bank_house"] = house
            item["bank_building"] = (
                (new_bldgs[i] if i < len(new_bldgs) else "").strip() or None
            )

        elif bank_raw:
            item["bank_id"] = int(bank_raw)
        else:
            # номер есть, банк не выбран — пропускаем строку
            if number:
                errors.append(f"Счёт #{i + 1}: выберите банк")
            continue

        accounts.append(item)

    return accounts, errors