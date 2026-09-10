
from datetime import date, datetime, timedelta


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
        # print("full_text", full_text)
        court_index = [full_text.index(i) for i in find_text if i in full_text][0] # получаем индкес наименования суда
        court_name = full_text[court_index:court_index + 3]
        # print("название суда", " ".join(court_name))
        return " ".join(court_name)

    @staticmethod
    def take_court_date(text: str) -> tuple[date, str, str] | None:
        """
        Получение даты заседания из текста.
        :return: date, str, str
        """
        print("ТЕКСТ ДЛЯ ВЫЯСНЕНИЯ ДАТЫ", text)
        list_text = text.split()
        find_index = list_text.index('Дата')
        find_text = list_text[find_index:]
        text_date, time_court, hall_court = find_text[5].replace(",", ""), find_text[6].replace(",", ""), find_text[-1]
        date_of_court = datetime.strptime(text_date, '%d.%m.%Y').date()
        print(f"дата суда: {date_of_court}, время: {time_court}, место: {hall_court}")

        if check_date(date_of_court):
            print("дата подходит для сохранения", date_of_court)
            return (date_of_court, time_court, hall_court) 
        
        return None

    @staticmethod
    def check_date_earlier(check_date: date) -> bool:
        """Проверка даты - 1 месяц"""
        current_month = datetime.now().date()
        date_earlier = current_month - timedelta(days=30)
        if check_date.month in (
            date_earlier.month, current_month.month) and check_date.year == current_month.year:
            return True
        return False

    @staticmethod
    def check_name_document(check_name: str) -> bool | None:
        """
        Поиск слов в названии документа, если есть слово "удовлетворить" - необходимо проставить статус
        """
        texts = ("удовлетворить",)
        for i in check_name.split(" "):
            if i.lower() in texts:
                print("Необходимо проставить статус. Есть слово Удовлетворить ")
                return True



def check_date(date_of_court: date) -> bool:
    """Проверка даты + 2 месяца"""
    date_now = date.today()
    one_month = date_now + timedelta(days=30)
    two_month = one_month + timedelta(days=30)

    if (
        (date_of_court.month == date_now.month and date_of_court.year == date_now.year) or
        (date_of_court.month == one_month.month and date_of_court.year == one_month.year) or
        (date_of_court.month == two_month.month and date_of_court.year == two_month.year)
    ):
        return True
    else:
        return False
