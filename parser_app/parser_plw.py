"""
Запуск User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
python -m parser.parser_plw
"""
import asyncio
from datetime import datetime

from httpx import TimeoutException
from playwright.async_api import async_playwright, Page, BrowserContext, expect

from config.db.db_config import get_db
from config.logger_config import parser_logger

from config.schemas.court_schema import CourtSessionSchema
from core.services.parser_saver_service import ParserDataSaver
from parser_app.dependency import create_parser_data_saver
from parser_app.utils.helpers import TextHepler
from parser_app.utils.sleep import random_sleep_for_search, random_sleep, random_start_sleep


class ParserKad:
    def __init__(self, url: str, case_number: str, data_saver: ParserDataSaver):
        # self.browser = self.setup_browser()
        """
        :param url: полный url адрес
        :param case_number: номер дела, например А52-542198
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
            await page.goto (self.url, timeout=10000)
            # user_agent = await page.evaluate("() => navigator.userAgent")
            return page
        
        except Exception as e:
            # Когда браузер открывает страницу, но не может закрыть всплывающее окно,
            # возникает ошибка TimeoutError: Timeout 10000ms exceeded.
            # Чтобы не прерывать работу парсера, мы перезагружаем страницу и продолжаем работу.
            parser_logger.error("Не удалось открыть страницу; Дело № %s: Ошибка %s", self.case_number, e)
            # await page.close()
            await page.reload()
            return page
            # return None

    async def run(self):
        """ Запуск парсера """
        self.page = await self.setup_for_page(self.context) # type: ignore
        if self.page is None:
            raise RuntimeError(f"Не удалось открыть страницу для {self.case_number}")
    
        await self.run_full_path()

    async def run_full_path(self):
        """ Полный путь через главную страницу """
        await self.promo_notification_popup_close()
        await self.enter_case_number()
        if await self.check_page():
            return
        await self.click_link_case()
        # Если не удалось перейти на новую страницу – завершаем и закрываем парсер
        if not self.new_page:
            await self.close_page()
            return
        
        # Раздел - поиск дат заседаний

        # Данный раздел закомментирован, так как если нет заседаний, то все-равно необходимо проверить документы
        # Если search_red_calendar вернул True – дальше не идём
        # if await self.search_red_calendar():
        #     return
        await self.search_red_calendar()
        
        # Раздел с поиском документа
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
            parser_logger.info("Всплывающее окно закрыто. Парсинг %s", self.case_number,
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
        for attempt in range(1, retries + 1):
            try:
                parser_logger.info(f"Попытка {attempt} — ищу поле для ввода номера дела: {self.case_number}")

                # Явное ожидание появления поля
                try:
                    input_field = self.page.get_by_placeholder('например, А50-5568/08')

                except AttributeError as attr_err:
                    parser_logger.error("Ошибка при поиске поля ввода номера дела: %s", attr_err)
                    await self.page.reload()
                    continue
                if input_field:
                    await input_field.fill(self.case_number)
                    await asyncio.sleep(2)
                    await input_field.press('Enter')

                    parser_logger.info("✅ Ввод номера дела успешно выполнен",
                                    extra={
                                        "case_number": self.case_number,
                                        "step": "enter_case_number",
                                        "system": "parser",
                                    })
                    return  # успех — выходим
                else:
                    parser_logger.warning("Поле для ввода номера дела не найдено на странице. Попытка %s", attempt)
                    await self.page.reload()
                    await asyncio.sleep(5)  # время на подгрузку

            except Exception as e:
                parser_logger.warning(f"⚠️ Ошибка при вводе номера дела на попытке {attempt}: {e}")

                if attempt < retries:
                    parser_logger.info("🔁 Обновляю страницу и повторяю попытку",
                                       extra={"step": "refresh_and_retry", "case_number": self.case_number})
                    await self.page.reload()
                    await asyncio.sleep(5)  # время на подгрузку
                else:
                    parser_logger.error("❌ Все попытки ввода номера дела исчерпаны",
                                        extra={
                                            "case_number": self.case_number,
                                            "step": "enter_case_number",
                                            "error": str(e),
                                            "system": "parser",
                                        })
                    
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

    async def search_name(self):
        """
        Получаем наименование должника из текста страницы. 
        Если наименование не совпадает, закрываем страницу.
        Если наименование совпадает, получаем ИНН должника для сохранения в бд
        """
        # Проверка содержимого текста респондента на примере дела А40-23673/2024
        try:
            respondent_cell = self.page.locator('td.respondent').filter(
            has_text='ООО "ИТМ ИНЖИНИРИНГ"')

            # print("respondent_cell", await expect(respondent_cell).to_contain_text('ООО "ИТМ ИНЖИНИРИНГ"'))
            # name = expect(respondent_cell).to_contain_text('ООО "ИТМ ИНЖИНИРИНГ"')

            # Имитируем наведение, чтобы показать скрытый блок
            await respondent_cell.hover()
            # или клик: await org.click()
            # Теперь скрытый span стал видимым
            hidden_span = respondent_cell.locator('span.js-rolloverHtml')
            # Получаем текст из скрытого содержимого (наименование, адрес, инн)
            text = await hidden_span.inner_text()
            # print("ИНН",inn_text)  # Содержит ИНН, адрес и т.д.
            text = TextHepler.split_text(text)

            name = TextHepler.take_name(text)
            inn = TextHepler.take_inn(text)
            print("Получил ИНН и название должника", inn, name)

        except Exception as e:
            print("Не нашел инн",e)

    async def click_link_case(self):
        """
        Обнаружение знака + для раскрытия данных о деле. 
        При клике будет открыта новая вкладка и осуществлен переход на нее.
        """
        try:
            case_number_link = self.page.locator("a[target='_blank'].num_case", has_text=self.case_number)
            
            # Проверяем текст по названию должника для удостоверения правильности страницы для дальнейшего парсинга
            # await self.search_name()
                
            await asyncio.sleep(random_sleep())
            # ожидаем открытия новой вкладки
            async with self.page.context.expect_page() as new_page:
                await case_number_link.click()

            self.new_page = await new_page.value
            parser_logger.info("Переход на новую страницу",
                               extra={
                                   "case_number": self.case_number,  # Основной идентификатор
                                   "step": "click_link_case",
                                   "system": "parser",
                               })

            return self.new_page

        except Exception as e:
            parser_logger.error("Ошибка при переходе на новую страницу %s", e)


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


async def process_parsing(browser, case: str, data_saver: ParserDataSaver):
    """ Запуск парсинга """
    context = await browser.new_context(
        viewport=None,  # Использовать размер экрана по умолчанию (как у обычного браузера)
        # user_agent=ua  # используем рандомный агент
    )
    parser = ParserKad(
        url='https://kad.arbitr.ru/', 
        case_number=case, 
        data_saver=data_saver
        )
    parser.context = context  # передаем context внутрь парсера
    await parser.run()  # запуск парсера
    await asyncio.sleep(random_start_sleep())
    await context.close()


async def run_playwright_parsing(case_number: str):
    """Обертка для запуска парсера из внешнего кода"""
    browser = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,  # True для безголового режима, False для визуального
                args=[
                    "--start-maximized",  # Окно на весь экран
                    "--disable-blink-features=AutomationControlled",  # Убираем флаг автоматизации
                    "--disable-infobars",  # Убираем сообщение "Chrome is being controlled"
                    "--disable-dev-shm-usage",  # Улучшаем работу в контейнерах
                    "--no-sandbox",  # Полезно в некоторых окружениях
                    "--disable-popup-blocking",
                    "--window-size=1920,1080"
                ],
                chromium_sandbox=False,
                ignore_default_args=["--enable-automation"],  # Отключаем automation флаг
            )
            async for uow in get_db(): 
                # async for получает первый и единственный uow
                # открывает сессию
                try:
                    data_saver = create_parser_data_saver(uow.session)
                    await process_parsing(browser, case_number, data_saver)
                finally:
                    # pass для избежания ошибки с Pylance 
                    # Python запрещает использовать break, continue или return внутри блока finally в async for
                    pass
                break   # выполняется после finally и закрывает соединение
    finally:
        if browser:
            await browser.close()
        

# asyncio.run(run_playwright_parsing("А40-23673/2024"))
