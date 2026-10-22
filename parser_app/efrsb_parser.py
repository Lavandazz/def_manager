import asyncio

from patchright.async_api import async_playwright, Page

from config.db.db_config import get_db

from config.settings_folders import BASE_FOLDER
from core.services.parsers.parser_sro_service import ParserSroDataSaver
from parser_app.dependency import create_parser_sro_data_saver
from config.logger_config import efrsb_logger
from parser_app.utils.helpers import TextHepler
from utils.exceptions import AccessForbidden

# Для корректной работы patchright с xvfb (виртуальным дисплеем) в контейнере Docker 
# xvfb - виртуальный графический дисплей, который позволяет запускать графические приложения (X-сервер) в среде без физического дисплея.
# Необхоим для обхода ошибок 403 на сайте efrsb, которые возникают при попытке открыть браузер без графического интерфейса. 
# Устанавливаем глобальные _playwright и _browser для того, чтобы браузер не закрывался в своем контейнере после завершения задачи парсинга.
# Для парсинга необходимо передавать контекст.

SCREEN_PATH = BASE_FOLDER.cwd() / "screens" / "screens_efrsb"

if not SCREEN_PATH.exists():
    SCREEN_PATH.mkdir(parents=True, exist_ok=True)


class ParserEFRSB:
    def __init__(self, url: str, person_name: str, user_id: int, data_saver: ParserSroDataSaver):
        self.url = url
        self.person_name = person_name
        self.user_id = user_id
        self.data_saver = data_saver
        self.page: Page = None # type: ignore

    async def setup_for_page(self, context):
        """ Открытие страницы """
        page = await context.new_page()
        try:
            response = await page.goto(
                self.url, 
                timeout=30000,
                wait_until="domcontentloaded",
                referer="https://old.bankrot.fedresurs.ru/Default.aspx",)

            if response.status == 403:
                efrsb_logger.debug(f"Открыта страница {self.url} для {self.person_name}, статус: {response.status}")
                await page.screenshot(path=f"{SCREEN_PATH}/403_page.png", full_page=True)
                efrsb_logger.debug(f"Скриншот страницы 403 сохранён в {SCREEN_PATH}/403_page.png")
                await page.close()
                return None

            return page
        
        except Exception as e:
            efrsb_logger.warning(f"Не удалось открыть {self.url}: {e}")
            await page.close()
            return None
    
    async def run(self):
        """ Запуск парсера """
        self.page = await self.setup_for_page(self.context) # type: ignore
        if self.page is None:
            raise AccessForbidden(f"Не удалось открыть страницу для {self.person_name}")
        # вызываем по-шаговый процесс парсинга c проверкой на ошибку 403
        check = await self._check_page()
        if check:
            efrsb_logger.error(f"Ошибка 403 при открытии страницы для {self.person_name}. Возможно, сайт заблокировал доступ.")
            await self.page.close()
        try:
            await self.process_parsing()
        finally:
            if self.page and not self.page.is_closed():
                await self.page.close()

    async def _check_page(self):
        await asyncio.sleep(4.5)
        print("URL:", self.page.url)
        print("Title:", await self.page.title())      

        await self.page.screenshot(path=f"{SCREEN_PATH}/main_page.png", full_page=True)
        html = await self.page.content()
        print("HTML length:", len(html))

        await asyncio.sleep(4.5)
 
        

    async def _process_parsing(self):
        """ Основной процесс парсинга """
        # ждем появления поля ввода фамилии
        await self.wait_selector("#ctl00_cphBody_ArbitrManagerList1_tbLastName")
        await self.fill_fio()

        await self.page.screenshot(path=f"{SCREEN_PATH}/fio_page.png", full_page=True)
        print(f"Скриншот сохранён в {SCREEN_PATH}/fio_page.png")

        # Получаем и сохраняем данные пользователя
        user_data = await self.get_text_data()
        efrsb_logger.info(f"получил данные из блока АУ")
        await self.update_user_data(user_data)
        # Получаем и сохраняем данные СРО
        sro_data = await self.get_sro_data()
        await self.save_user_sro_data(sro_data)

    async def process_parsing(self):
        await self._process_parsing()

    async def wait_selector(self, selector: str):
        """Ожидание появления элемента на странице"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
        except Exception as e:
            efrsb_logger.warning(f"Не удалось найти элемент {selector}: {e}")

    async def _fill_surname(self, surname: str):
        """ Заполнение фамилии """
        try:
            await self.page.fill("#ctl00_cphBody_ArbitrManagerList1_tbLastName", surname)
            await asyncio.sleep(3.5)  # ожидание для завершения всех действий на странице
        except Exception as e:
            efrsb_logger.error(f"Не удалось заполнить фамилию {surname}: {e}")

    async def _fill_name(self, name: str):
        """ Заполнение имени """
        try:
            await self.page.fill("#ctl00_cphBody_ArbitrManagerList1_tbFirstName", name)
            await asyncio.sleep(3.8)  # ожидание для завершения всех действий на странице
        except Exception as e:
            efrsb_logger.error(f"Не удалось заполнить имя {name}: {e}")

    async def _fill_patronymic(self, patronymic: str):
        """ Заполнение отчества """
        try:
            await self.page.fill("#ctl00_cphBody_ArbitrManagerList1_tbMiddleName", patronymic)
            await asyncio.sleep(4.2)  # ожидание для завершения всех действий на странице

        except Exception as e:
            efrsb_logger.error(f"Не удалось заполнить отчество {patronymic}: {e}")

    async def _press_search_button(self):
        """ Нажатие кнопки поиска """
        try:
            search_btn = self.page.locator("#ctl00_cphBody_ArbitrManagerList1_ibArmSearch")
            if search_btn:
                await search_btn.click()        
                await asyncio.sleep(2.7)  # ожидание для завершения всех действий на странице
            else:
                await self.page.get_by_title("Поиск").click()
                efrsb_logger.debug(f"нажал кнопку Поиск : ")

        except Exception as e:
            efrsb_logger.error(f"ОШИБКА при нажатии кнопки поиска: {e}")

    async def _press_link(self, link: str, name_link: str):
        try:
            await self.page.click(link)
        except Exception as e:
            efrsb_logger.error(f" _press_link Не удалось нажать ссылку {name_link}: {e}")  
            await asyncio.sleep(3)
            await self.page.close()

    async def press_link(self, link: str, name_link: str):
        """
        Нажатие на ссылку.
        link: ссылка
        name_link: наименование ссылки для отображение в логере
        """
        await asyncio.sleep(3.3)
        await self._press_link(link, name_link)

    async def press_btn(self, selector: str | None = None):
        """ Нажатие кнопки """
        if selector is None:
            await self._press_search_button()
        else:
            try:
                await self.page.click(selector)
                await asyncio.sleep(3.5)  # ожидание для завершения всех действий на странице

            except Exception as e:
                efrsb_logger.error(f"Не удалось нажать кнопку {selector}: {e}")

    async def fill_fio(self):
        """
        Заполнение полей на портале (ФИО)
        """
        surname, name, patronymic = TextHepler.get_person_data(self.person_name)
        await self._fill_surname(surname)
        await self._fill_name(name)
        await self._fill_patronymic(patronymic)
        await self.press_btn()

    async def _get_person_data(self) -> dict:
        """
        Парсинг блока с информацией об управляющем.
        Получение данных по строкам, сохранение данных в словарь.
        """
        await asyncio.sleep(5.5)
        
        fields = {
            "inn":        "#ctl00_cphBody_trInn",
            "snils":      "#ctl00_cphBody_trSnils",
            "reg_num":    "#ctl00_cphBody_trRegNumFrs",
            "reg_date":   "#ctl00_cphBody_trRegDate",
            "date_begin": "#ctl00_cphBody_trDateBegin",
        }
        data = {}
        for key, loc in fields.items():
            try:
                text = await self.page.locator(f"{loc} td:last-child").inner_text()
                data[key] = text.strip()
            except Exception as e:
                data[key] = None
                efrsb_logger.error(f"Не удалось прочитать ключ {key}: {e}")
        
        try:
            data["sro_name"] = (await self.page
                .locator("#ctl00_cphBody_trSroName td:last-child a")
                .inner_text()).strip()
        except Exception:
            data["sro_name"] = None

        efrsb_logger.debug(f"Получение даных с сайта {data}")
        return data

    async def get_text_data(self) -> dict:
        """
        Получение данных о арбитражном управляющем. 
        1) Нажатие на ссылку ФИО 
        2) Парсинг данных из блока Карточки арбитражного управляющего
        3) Возвращение готового словаря с данными
        """
        await self.press_link("a[title='Карточка арбитражного управляющего']", "fio_person")
        return await self._get_person_data()

    async def update_user_data(self, data: dict):
        """
        Обновление данных АУ в бд
        """
        await self.data_saver.save_user_data(user_id=self.user_id, user_data=data)

    async def _get_sro_data(self) -> dict:
        """Сбор данных с карточки СРО."""
        await self.page.wait_for_selector("#ctl00_cphBody_tblSroCardInfo", timeout=10000)

        fields = {
            "name":                         "#ctl00_cphBody_trName",
            "reg_num":                      "#ctl00_cphBody_trRegNum",
            "reg_date":                     "#ctl00_cphBody_trRegDate",
            "inn":                          "#ctl00_cphBody_trInn",
            "ogrn":                         "#ctl00_cphBody_trOgrn",
            "ur_address_sro":               "#ctl00_cphBody_trUrAddressSro",
            "phone":                        "#ctl00_cphBody_trPhone",
            "email":                        "#ctl00_cphBody_trEmail",
            "url":                          "#ctl00_cphBody_trUrl",
        }

        data = {}
        for key, row_sel in fields.items():
            cell = self.page.locator(f"{row_sel} td:last-child")
            if await cell.count() == 0:          # строки нет — не ждём 30 сек
                data[key] = None
                continue
            try:
                data[key] = (await cell.inner_text(timeout=2000)).strip()
            except Exception as e:
                data[key] = None
                efrsb_logger.error(f"Не удалось прочитать {key}: {e}")

        # Ссылка на список управляющих — отдельно
        try:
            data["managers_list_url"] = await self.page.locator(
                "#ctl00_cphBody_hlAuList"
            ).get_attribute("href")
        except Exception:
            data["managers_list_url"] = None
        efrsb_logger.debug(f"Получены данне о СРО: {data}")

        return data        

    async def get_sro_data(self) -> dict:
        """
        Получение данных о СРО
        """
        await self.press_link("#ctl00_cphBody_lnkSro", "sro")
        await asyncio.sleep(4.6)
        data = await self._get_sro_data()
        return data

    async def save_user_sro_data(self, sro_data: dict):
        """
        Сохранение данных о СРО в базу данных и пользователя
        """
        return await self.data_saver.save_user_sro_data(sro_data, self.user_id)


async def process_parsing(browser, person_name: str, user_id: int, data_saver: ParserSroDataSaver):
    """ Запуск парсинга """
    context = await browser.new_context()
    parser = ParserEFRSB(
        url='https://old.bankrot.fedresurs.ru/ArbitrManagersList.aspx', 
        person_name=person_name,
        user_id=user_id,
        data_saver=data_saver,
        )
    parser.context = context  # передаем context внутрь парсера
    await parser.run()  # запуск парсера
    await asyncio.sleep(4.6)  # ожидание для завершения всех действий на странице
    await context.close()


async def run_efrsb_parsing(user_id: int, person_name: str):
    """Обертка для запуска парсера из внешнего кода"""
    browser = None
    try:

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # True для безголового режима, False для визуального
                args=[
                    # "--start-maximized",  # Окно на весь экран
                    "--disable-blink-features=AutomationControlled",  # Убираем флаг автоматизации
                    "--disable-infobars",  # Убираем сообщение "Chrome is being controlled"
                    "--disable-dev-shm-usage",  # Улучшаем работу в контейнерах
                    "--no-sandbox",  # Полезно в некоторых окружениях
                    "--disable-popup-blocking",
                    # "--window-size=1920,1080"
                ],
                chromium_sandbox=False,
                ignore_default_args=["--enable-automation"],  # Отключаем automation флаг
            )
            async for uow in get_db(): 
                # async for получает первый и единственный uow
                # открывает сессию
                try:
                    data_saver = create_parser_sro_data_saver(uow.session)
                    await process_parsing(browser, person_name, user_id, data_saver)
                finally:
                    # pass для избежания ошибки с Pylance 
                    # Python запрещает использовать break, continue или return внутри блока finally в async for
                    pass
                break   # выполняется после finally и закрывает соединение

    finally:
        if browser:
            await browser.close()
