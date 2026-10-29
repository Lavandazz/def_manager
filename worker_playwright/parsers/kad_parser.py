"""
Запуск User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
python -m parser.parser_plw
"""
import asyncio
from datetime import datetime

from httpx import TimeoutException
from playwright.async_api import Page, BrowserContext

from shared.config.logger_config import parser_logger
from shared.config.schemas.court_schema import CourtSessionSchema
from shared.config.settings_folders import BASE_FOLDER
from shared.core.services.parsers.parser_saver_service import ParserDataSaver
from shared.utils.text_helpers import TextHepler
from shared.utils.sleep_helper import random_sleep_for_search, random_sleep

SCREEN_PATH = BASE_FOLDER.cwd() / "screens" / "screens_kad"

if not SCREEN_PATH.exists():
    SCREEN_PATH.mkdir(parents=True, exist_ok=True)

class ParserKad:
    def __init__(self, url: str, case_number: str, data_saver: ParserDataSaver):
        """
        :param url: полный url адрес
        :param case_number: номер дела, например А52-542198
        :param data_saver: класс для работы с БД для сохранения полученных данных
        :param page: главная страница
        :param new_page: страница для парсинга дела
        :param context: context настройки браузера
        """
        self.url: str = url
        self.case_number: str = case_number
        self.data_saver = data_saver # передаем зависимость для сохранения данных о судах
        self.page: Page = None
        self.new_page: Page = None
        self.context: BrowserContext = None 

    async def setup_for_page(self, context):
        """ Открытие страницы """
        page = await context.new_page()
        try:
            await page.goto(self.url, timeout=15000, wait_until="domcontentloaded")
            # user_agent = await page.evaluate("() => navigator.userAgent")
            return page
        
        except Exception as e:
            # Когда браузер открывает страницу, но не может закрыть всплывающее окно,
            # возникает ошибка TimeoutError: Timeout 10000ms exceeded.
            # Чтобы не прерывать работу парсера, мы перезагружаем страницу и продолжаем работу.
            parser_logger.warning(f"Не удалось открыть страницу; Дело № {self.case_number}: Ошибка {e}")

            try:
                parser_logger.debug(f"Еще перезагрузка : {self.case_number}")
                await page.reload(timeout=10000, wait_until="domcontentloaded")
                # await page.reload()

                await page.wait_for_selector('input[placeholder="например, А50-5568/08"]', timeout=15000)
                print("дождался жлемента")

            except Exception as e2:
                # сли страница не готова, закрываем парсер и страницу
                parser_logger.error("Reload тоже не удался: %s", e2)
                await page.close()
                return None 
            
            return page

    async def run(self):
        """ Настройки страницы и запуск парсера """
        self.page = await self.setup_for_page(self.context) # type: ignore
        if self.page is None:
            parser_logger.error(f"Ошибка RuntimeError: {self.case_number}")
             
            raise RuntimeError(f"Не удалось открыть страницу для {self.case_number}")
    
        await self.run_full_path()

    async def run_full_path(self):
        """ 
        Полный путь парсинга:
        :promo_notification_popup_close: Закрытие всплывающего окна. Если не получилось закрыть, то происходит reload страницы без окна.
        :enter_case_number: Ввод номера дела в окно ввода.
        :check_page: Проверка страницы на текст 'Нет результатов', если текст есть, значит введено не верное дело - происходит закрытие парсера.
        :click_link_case: Клик по ссылке номера дела, установка self.new_page - как новая страница.
        :if not self.new_page: проверка существования новой страницы, либо закрытие парсера.
        :search_and_save_date_case: Получение даты решения дела в суде и сохранение в бд.
        :search_red_calendar: Поиск текста 'Следующее заседание' и раскрытие данных нажатием на +, если текста нет - дело считается не активным и закрывается браузер
        :click_online_case: Поиск кнопки 'Электронное дело' и переход к парсингу ответов от суда. 
        :parse_mod: Сбор информации об ответах от судов. (Дата ответа, наименование суда, наименование документа)
        :close_page: Закрытие парсера.
        """
        await self.promo_notification_popup_close()
        await self.enter_case_number()
        if await self.check_page():
            return

        await self.click_link_case() # Клик по ссылке номера дела, установка self.new_page - как новая страница

        if not self.new_page:        # Если не удалось перейти на новую страницу – завершаем и закрываем парсер
            await self.close_page()
            return
        
        # ====== Раздел - поиск даты дела ======
        await self.search_and_save_date_case()

        # ====== Раздел - поиск дат заседаний ======
        await self.search_red_calendar()
        
        # ====== Раздел с поиском документа ======
        await self.click_online_case()
        await self.parse_mod()
        await self.close_page()

    async def promo_notification_popup_close(self):
        """
        Метод для закрытия всплывающего окна.
        Окно появляется не всегда, игнорируем ошибку 
        """
        if self.page is None:
            parser_logger.warning(
                "promo_notification_popup_close: page is None, пропускаем",
                extra={"case_number": self.case_number, "step": "popup_close", "system": "parser"},
            )
            return
        try:
            close_btn = self.page.locator('a.b-promo_notification-popup-close')
            await close_btn.wait_for(state='visible')
            await close_btn.click()


            parser_logger.info(f"Всплывающее окно закрыто. Парсинг {self.case_number}", 
                            extra={
                                "case_number": self.case_number,  # Основной идентификатор
                                "step": "popup_close",
                                "system": "parser",
                            })

        except Exception as e:
            parser_logger.warning(f"Ошибка при закрытии всплывающего окна: {e}",
                                extra={
                                    "case_number": self.case_number,  # Основной идентификатор
                                    "step": "popup_close",
                                    "error": e,
                                    "system": "parser",
                                })
            # await self.page.reload()  # обновляем страницу, если окно не закрылось

    async def enter_case_number(self, retries: int = 3):
        """
        Метод для ввода номера дела с попытками и обновлением страницы,
        так как страница иногда подвисает. 
        Если ввода номера не произошло, то страница обновится (await self.page.reload())
        :param retries: Количество попыток ввода дела
        """
        await asyncio.sleep(5.3)
        input_field = self.page.get_by_placeholder('например, А50-5568/08')
        search_button = self.page.get_by_role("button", name="Найти")
        for attempt in range(1, retries + 1):
            try:
                parser_logger.info(f"Попытка {attempt} — ищу поле для ввода номера дела: {self.case_number}")
                
                await input_field.fill(self.case_number)
                await asyncio.sleep(3.7)
                await search_button.hover()
                # await input_field.press('Enter')
                parser_logger.debug(f"навел на кнопку Найти и делаю скрин")
                await self.page.screenshot(path=SCREEN_PATH / f"{self.case_number}_hover.png", full_page=True)
                await asyncio.sleep(2.9)
                await search_button.click()
                await self.page.screenshot(path=SCREEN_PATH / f"{self.case_number}_click.png", full_page=True)

                parser_logger.info("✅ Ввод номера дела успешно выполнен",
                                   extra={
                                       "case_number": self.case_number,
                                       "step": "enter_case_number",
                                       "system": "parser",
                                   })
                await asyncio.sleep(2.8)
                await self.page.screenshot(path=SCREEN_PATH / f"{self.case_number}_after_click.png", full_page=True)
                return  # успех — выходим

            except Exception as e:
                parser_logger.warning(f"⚠️ Ошибка при вводе номера дела на попытке {attempt}: {e}")

                if attempt < retries:
                    parser_logger.info("🔁 Обновляю страницу и повторяю попытку",
                                       extra={"step": "refresh_and_retry", "case_number": self.case_number})
                    # await self.page.reload()
                    await input_field.focus()
                    await asyncio.sleep(2.3)
                    parser_logger.debug(f"Сфокусировался на поле дела и делаю скрин перед нажатием на ENTER")
                    await self.page.screenshot(path=SCREEN_PATH / f"{self.case_number}_hover.png", full_page=True)
                    await input_field.press('Enter')
                    await asyncio.sleep(5)  # время на подгрузку
                    parser_logger.warning(f"Клик по кнопке Найти ")

                    # await search_button.click()
                else:
                    parser_logger.error("❌ Все попытки ввода номера дела исчерпаны",
                                        extra={
                                            "case_number": self.case_number,
                                            "step": "enter_case_number",
                                            "error": str(e),
                                            "system": "parser",
                                        })
                    

    async def click_link_case(self):
        """
        Клик по ссылке на номер дела после его поиска.
        """
        try:
            case_number_link = self.page.locator("a[target='_blank'].num_case", has_text=self.case_number)
            
            await asyncio.sleep(random_sleep())
            parser_logger.debug(f"Нашел ссылку на дело case_number_link, делаю клик по нему {case_number_link}") 
            href = await case_number_link.get_attribute("href")
            parser_logger.debug("href = %s", href)
            
            # ожидаем открытия новой вкладки
            async with self.page.context.expect_page() as new_page:
                await case_number_link.click()

            parser_logger.debug(f"Кликнул по ссылке дела, {new_page.value}")

            await self.page.screenshot(path=f"{SCREEN_PATH}/{self.case_number}_link.png", full_page=True)

            self.new_page = await new_page.value
            await self.new_page.wait_for_load_state("domcontentloaded")
            current_url = self.new_page.url  # получаем адрес новой странички

            # Сохраняем ссылку на дело в базу данных
            await self._save_link_case(case_number=self.case_number, link=current_url)  # сохраняем ссылку в бд
            
            parser_logger.info("Переход на новую страницу",
                               extra={
                                   "case_number": self.case_number,  # Основной идентификатор
                                   "step": "click_link_case",
                                   "system": "parser",
                               })

            return self.new_page

        except Exception as e:
            parser_logger.error(f"Ошибка при переходе на новую страницу {e}")
    
    async def check_page(self):
        """
        Метод проверяет существование данных по номеру дела.
        Если номер дела не верный, будет отображено 'Нет результатов' и браузер закроется
        """
        await asyncio.sleep(1)
        no_results = self.page.get_by_text('Нет результатов', exact=True)
        btn = self.page.get_by_role("button", name="Отправить запрос")

        if await no_results.is_visible() and await btn.is_visible():
            await self.close_page()
            return True  # Возвращаем True, чтобы прервать выполнение
        return False


    async def _search_date_case(self):
        """
        Получаем дату решения дела в суде. 
        """
        try:
            date_case = self.page.locator('div.bankruptcy')
            date_text = await date_case.inner_text()
            parser_logger.debug(f"Дата документа найдена, {date_case}",)
            return date_text

        except Exception as e:
            return None

    async def _save_date_case(self, case_number, case_date):
        """
        Сохраняем дату решения дела в базе данных
        """
        try:
            if case_date:
                await self.data_saver.save_case_date(case_number=case_number, date_case=case_date)
                parser_logger.info(f"Сохранил дату решения {case_date} для дела {case_number}",
                                    extra={"case_number": self.case_number, 
                                    "step": "save_date_case",
                                    "system": "parser",
                                })
            else:
                parser_logger.info(f"Дата дела case_date не найдена или не соответствует: {case_date}, делаю скрин")
                await self.page.screenshot(path=f"{SCREEN_PATH}/{self.case_number}_no_case_date.png", full_page=True)

        except Exception as e:
            parser_logger.error("Ошибка при сохранении даты дела", e)
            pass

    async def search_and_save_date_case(self):
        """
        Получаем дату решения дела в суде и сохраняем в бд
        """
        date_case = await self._search_date_case()
        parser_logger.debug(f"Найдена дата дела: {date_case}")
        await self._save_date_case(case_number=self.case_number, case_date=date_case)

        
    async def _save_link_case(self, case_number, link):
        """
        Сохраняем ссылку на дело в базе данных
        """
        try:
            await self.data_saver.save_case_link(case_number=case_number, link=link)
            parser_logger.info(f"Сохранил ссылку на дело {link}",
                               extra={
                                   "case_number": self.case_number,  # Основной идентификатор
                                   "step": "save_link_case",
                                   "system": "parser",
                               })
        except Exception as e:
            parser_logger.error("Ошибка при сохранении ссылки на дело", e)
            pass


    async def search_red_calendar(self):
        """
        Поиск знака обознакчения 'Следующее заседание' и раскрытие данных нажатием на +.
        Если обозначения 'Следующее заседание' нет,  дело считается не активным и закрывается браузер
        """
        try:
            await asyncio.sleep(random_sleep_for_search())
            search_lines = await self.new_page.locator('.b-chrono-item-header').all()
            for line in search_lines:
                text = await line.inner_text()
                if 'Следующее заседание:' in text:
                    # span class "instantion-name" в строке с заседанием
                    # Достаем наименование суда из текста
                    court_name = TextHepler.take_court_name(text=text)

                    collapse_block = line.locator('.b-collapse[title*="ознакомиться"]')
                    plus_button = collapse_block.locator('i.b-sicon') # поиск плюсика для раскрытия всех заседаний и доков
                    await collapse_block.scroll_into_view_if_needed()
                    await asyncio.sleep(random_sleep_for_search())
                    await plus_button.click()
                    parser_logger.info("Нажатие на плюсик",
                                       extra={
                                           "case_number": self.case_number,  # Основной идентификатор
                                           "step": "search_red_calendar",
                                           "system": "parser",
                                       })
                    # поочередно вызываем сохранение дат заседаний
                    # Получаем список из кортежей (дата, время, кабинет)
                    date_courts = await self.date_of_the_court_session()
                    if date_courts:
                        await self.save_court(court_name=court_name, list_court_date=date_courts)

                        return False # продолжаем парсинг
                
            # Если цикл закончился и строка не найдена
            parser_logger.info("Текста 'Следующее заседание' - нет. Закрываю дело.",
                           extra={
                               "case_number": self.case_number,
                               "step": "search_red_calendar",
                               "system": "parser",})
            await self.close_page()
            return True  # прерываем парсинг

        except Exception as e:
            parser_logger.exception(f"Ошибка в search_red_calendar {e}",
                        extra={"case_number": self.case_number, "step": "search_red_calendar", "system": "parser"})

    async def date_of_the_court_session(self) -> list | bool | None:
        """
        Поиск дат заседаний
        """
        try:
            # ожидаем появления элементов
            await self.new_page.wait_for_selector('.additional-info', state='visible', timeout=30000)
            dates_court = await self.new_page.locator('.additional-info').all_inner_texts() # Поиск всех дат заседаний
            if dates_court:
                result = []
                for el in dates_court:
                    if 'дата и время' in el.lower():
                        date_court: tuple | None = TextHepler.take_court_date(el)
                        if date_court:
                            result.append(date_court)  # сохраняем в список кортежи из даты, времени, кабинета 
                        # сохраняем в базу наименование суда в Court и CourtSession
                        # await save_court_date(el, self.case_number)
                print("Результат парсинга дат заседаний",result)
                return result
                        

            parser_logger.info("Заседаний нет")
            return False

        except Exception as e:
            print("Ошибка сохранения календаря", e)
            parser_logger.error("Ошибка сохранения календаря",
                                extra={
                                    "case_number": self.case_number,  # Основной идентификатор
                                    "step": "save_court_session",
                                    "error": e,
                                    "system": "parser",
                                })
    async def save_court(self, court_name, list_court_date):
        for court in list_court_date:
            court_schema = CourtSessionSchema(
                court=court_name, 
                date_court=court[0],
                time_court=court[1],
                hall_court=court[2]
            )
            print("Передаю схему для сохранения", court_schema)
            await self._save_court(
                court_name=court_schema.court, 
                case_number=self.case_number,
                date_court=court_schema.date_court,
                time_court=court_schema.time_court,
                hall_court=court_schema.hall_court,
                data_saver=self.data_saver
                )

    async def _save_court(self, court_name, case_number, date_court, time_court, hall_court, data_saver: ParserDataSaver):
        await data_saver.save_court_data(court_name, case_number, date_court, time_court, hall_court)


    async def click_online_case(self):
        """
        Поиск и клик по кнопке 'Электронное дело'
        """
        await asyncio.sleep(random_sleep())
        try:
            chrono_button = self.new_page.get_by_text('Электронное дело')
            await asyncio.sleep(1)
            await chrono_button.scroll_into_view_if_needed()
            await chrono_button.click()
            parser_logger.info("Клик по Электронному делу",
                               extra={
                                   "case_number": self.case_number,  # Основной идентификатор
                                   "step": "click_online_case",
                                   "system": "parser",
                               })
        
        except TimeoutException as e:
            parser_logger.error("Ошибка сохранения календаря %s", e,
                                extra={
                                    "case_number": self.case_number,  # Основной идентификатор
                                    "step": "click_online_case",
                                    "error": e,
                                    "system": "parser",
                                })
            
        except Exception as e:
            parser_logger.error("Ошибка сохранения календаря %s", e,)

    async def parse_mod(self):
        """
        Сбор информации об ответах от судов
        Дата ответа, наименование суда, наименование документа
        """
        await asyncio.sleep(random_sleep_for_search())
        try:
            date_items = await self.new_page.locator(".b-case-chrono-ed-item-date").all_inner_texts()
            declarers = await self.new_page.locator('.b-case-chrono-ed-item-declarers').all_inner_texts()
            documents = await self.new_page.locator('.b-case-chrono-ed-item-link').all_inner_texts()
            cnt = 0
            for i, date in enumerate(date_items):
                date = datetime.strptime(date, "%d.%m.%Y").date()
                # parser_logger.debug("+++++++ проверяю ответ от суда с датой %s", date)
                if TextHepler.check_date_earlier(date):
                    cnt += 1
                    TextHepler.check_name_document(check_name=documents[i])

                    parser_logger.debug(f"Сохраняю ответ с датой {date}")
                    
                    await self.data_saver.save_documents(
                        case_number=self.case_number, 
                        date=date, 
                        declarer=declarers[i], 
                        document_name=documents[i]
                        )
                    parser_logger.info("Ответы сохранил %s", date)
            if cnt == 0:     
                parser_logger.info("Подходящих ответов нет")
            

        except Exception as e:
            parser_logger.error("Ошибка парсинга ответов",
                                extra={
                                    "case_number": self.case_number,  # Основной идентификатор
                                    "step": "parse_mod",
                                    "error": e,
                                    "system": "parser",
                                })

    async def close_page(self):
        """
        Принудительное закрытие страницы
        """
        parser_logger.info(f'Закрываю парсер, страницы, {self.case_number}')
        if self.page:
            await self.page.close()
        if self.new_page:
            await self.new_page.close()
