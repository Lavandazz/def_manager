
from marmel_grammar import MarmelGrammar

from config.db.models import Bank, Debtor


class TextHelper:
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
        snils = str(snils)
        return f"{snils[:3]}-{snils[3:6]}-{snils[6:9]} {snils[9:]}"

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
        if birth:
            return f"""{
                f"{debtor.birth_region.region.region_name}," if debtor.birth_region.region.region_name else ""
                } г.{debtor.birth_region.city}"""
        
        return f"""{
                f"{debtor.residential_address.region.region_name}," if debtor.residential_address.region.region_name else ""
                } г.{debtor.residential_address.region.city}, {debtor.residential_address.address.street}, д. {
                                            debtor.residential_address.address.house} {
                                                debtor.residential_address.address.building if debtor.residential_address.address.building else ""
        } {f"кв.{debtor.residential_address.flat}" if debtor.residential_address.flat else ""}"""

    
text_helper = TextHelper()
