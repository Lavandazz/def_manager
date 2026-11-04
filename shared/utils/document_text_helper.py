from datetime import date
from marmel_grammar import MarmelGrammar
from shared.config.db.models import Bank, Debtor


class DocumentHelper:
    """
    Класс для изменения текстового представления в документах.
    Создает экземпляр для работы с падежами, выявления рода имен
    """
    def __init__(self):
        self.grammar = MarmelGrammar()

    def get_gender(self, name) -> str:
        """Определение пола человека для склонения слов"""
        return self.grammar.detect_gender(name)

    def get_decline_name(self, full_name) -> str:
        """
        Склонение полного ФИО с помощью библиотеки marmel_grammar
        Например, Иванова Ивана Ивановича
        """
        full_name_split = full_name.split()
        gen = self.get_gender(full_name_split[1]) # определение пола человека
        name = [self.grammar.decline(i.capitalize(), "gen", gender=gen) for i in full_name_split]
        if gen == "male":
            return " ".join(name), "уроженец", "несостоятельным"
        else:
            return " ".join(name), "уроженка", "несостоятельной"
        
    @staticmethod
    def get_short_name(full_name) -> str:
        """ Возрват строки вида Иванов И.И. """
        name = full_name.split()
        short_name = f"{name[0]} {name[1][0].capitalize()}.{name[2][0].capitalize()}."
        return short_name

    @staticmethod
    def get_initials(full_name) -> str:
        """ Возврат строки ФИО для шаблонов запросов по имуществу должника """
        name = full_name.split()
        return f"{name[0][0]}{name[1][0].capitalize()}{name[2][0].capitalize()}"
    
    @staticmethod
    def snils_str(snils: int) -> str:
        str_snils = str(snils)
        return f"{str_snils[:3]}-{str_snils[3:6]}-{str_snils[6:9]} {str_snils[9:]}"

    @staticmethod
    def get_bank_address_str(bank: Bank) -> str:
        bank_address = f"""{
            bank.mail_address.mail_index
            },{f"{bank.mail_address.region.region_name}," if bank.mail_address.region.region_name else ""} г.{bank.mail_address.region.city}, {bank.mail_address.address.street}, д. {bank.mail_address.address.house} 
        {bank.mail_address.address.building if bank.mail_address.address.building else ""}
        """
        return bank_address
    
    @staticmethod
    def get_debtor_address_str(debtor: Debtor, birth: bool) -> str:
        """
        Создаение строки адреса регистрации и адреса рождения для должника.
        Используется на странице отображения информации о должнике
        """
        if birth:
            region = debtor.birth_region
            if region is None:
                return ""  # или "не указано"
            prefix = f"{region.region_name}, " if region.region_name else ""
            return f"{prefix}г. {region.city}"

        res = debtor.residential_address
        if res is None:
            return ""  # или "не указано"

        region = res.region
        addr = res.address

        prefix = f"{region.region_name}, " if region.region_name else ""
        building = f" {addr.building}" if addr.building else ""
        flat = f" кв.{res.flat}" if res.flat else ""

        return f"{prefix}г. {region.city}, {addr.street}, д. {addr.house}{building}{flat}"

    @staticmethod
    def _debtor_to_form(d) -> dict:
        """попощь в выоде в форму документа"""
        return {
            "debtor_type": d.debtor_type.value if d.debtor_type else "",
            "name": d.name or "",
            "inn": str(d.inn) if d.inn else "",
            "snils": str(d.snils) if d.snils else "",
            "birthday": d.birthday.isoformat() if d.birthday else "",
            "birth_region": str(d.birth_region) if d.birth_region else "",
            "residential_address": str(d.residential_address) if d.residential_address else "",
        }
    
    @staticmethod
    def return_date(date_str: str) -> date:
        """
        Преобразует строку в объект datetime.date
        :param date_str: строка с датой в формате "дд.мм.гггг"
        :return: объект datetime.date
        """
        day, month, year = map(int, date_str.split('.'))
        return date(year, month, day)
    
document_helper = DocumentHelper()
