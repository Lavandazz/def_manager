from ast import pattern
from datetime import date, datetime, timedelta
import re


class TextHepler:
    @staticmethod
    def split_text(text) -> list:
        return text.replace("  ", "").split(",")

    @staticmethod
    def take_inn(text: list) -> int:
        return int([i for i in text if "ИНН" in i][0].split(":")[-1].strip())

    @staticmethod
    def take_name(text: list) -> str:
        return text[0] 

    @staticmethod
    def take_court_name(text: str) -> str:
        """Поиск названия суда из строки парсинга"""
        find_text = ["АС", "Верховный", "арбитражный", "Первая"]
        full_text = text.split()
        print("full_text", full_text)
        court_index = [full_text.index(i) for i in find_text if i in full_text][0] # получаем индкес наименования суда
        court_name = full_text[court_index:court_index + 3]
        print("название суда", " ".join(court_name))
        return " ".join(court_name)

    @staticmethod
    def take_court_date(text: str):
        """Получение даты заседания из текста"""
        print("ТЕКСТ ДЛЯ ВЫЯСНЕНИЯ ДАТЫ", text)
        list_text = text.split()
        find_index = list_text.index('Дата')
        find_text = list_text[find_index:]
        text_date, text_time, text_hall = find_text[5].replace(",", ""), find_text[6].replace(",", ""), find_text[-1]
        print(f"дата суда: {text_date}, время: {text_time}, место: {text_hall}")

        date_of_court = datetime.strptime(text_date, '%d.%m.%Y').date()
        print("date_of_court", date_of_court)
        if check_date(date_of_court):
            print("дата подходит для сохранения", date_of_court)


def check_date(date_of_court: date):
    """Проверка даты + 2 месяца"""
    date_now = date.today()
    one_month = date_now + timedelta(days=30)
    two_month = one_month + timedelta(days=30)

    if (
        (date_of_court.month == date_now.month and date_of_court.year == date_now.year) or
        (date_of_court.month == one_month.month and date_of_court.year == one_month.year) or
        (date_of_court.month == two_month.month and date_of_court.year == two_month.year)
    ):
        print(f'Сохранение дат судебных заседаний: {date_of_court}')
        return True
    else:
        print(f'Даты не сохранил: {date_of_court}')
        return False


