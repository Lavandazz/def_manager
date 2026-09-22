from datetime import date

from pydantic import BaseModel, ConfigDict

from config.db.models import DebtorType



class AccountSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: str


class BankSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    mail_address: MailAddress
    accounts: AccountSchema



class RegionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    region_name : str | None = None
    city: str
    


class AddressSchema (BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    street: str
    house: str
    building: str | None = None


class MailAddress(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    mail_index: int
    region: RegionSchema
    address: AddressSchema


class ResidentialAddress(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    region: RegionSchema
    address: AddressSchema
    flat: int | None = None

class DebtorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    debtor_type: DebtorType
    name: str
    inn: int | None = None
    snils: str | None = None
    birthday: date | None = None
    birth_region: RegionSchema | None = None
    residential_address: ResidentialAddress | None = None


class DebtorDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    debtor: DebtorSchema
    accounts: list[AccountSchema]
