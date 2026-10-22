from pydantic import BaseModel


class GenerateFormData(BaseModel):
    template: str                      # "requests" | "bank"
    region_court: str = "Московской области"
    debtor_full_name: str = ""
    debtor_birthday: str = ""
    debtor_snils: str = ""
    debtor_inn: str = ""
    debtor_birth_address: str = ""
    debtor_address: str = ""
    case_number: str = ""
    case_date: str = ""
    request_date: str = ""
    date_for: str = ""
    bank_name: str = ""