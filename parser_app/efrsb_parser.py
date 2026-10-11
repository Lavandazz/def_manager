import asyncio

from playwright.async_api import async_playwright, Page
from config.logger_config import efrsb_logger


class ParserEFRSB:
    def __init__(self, url: str, person_name: str):
        self.url = url
        self.person_name = person_name
        self.page: Page = None

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
            efrsb_logger.exception("Не удалось открыть страницу; ", e)
            # await page.close()
            await page.reload()
            return page
    
    async def run(self):
        """ Запуск парсера """
        self.page = await self.setup_for_page(self.context) # type: ignore
        if self.page is None:
            raise RuntimeError(f"Не удалось открыть страницу для {self.person_name}")
        # вызываем по-шаговый процесс парсинга 
        await self.process_parsing()


    async def _process_parsing(self):
        """ Основной процесс парсинга """
        # ждем появления поля ввода фамилии
        await self.wait_selector("#ctl00_cphBody_ArbitrManagerList1_tbLastName")
        await self.fill_fio()
        await self.get_text_data()
        await self.get_sro_data()

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
        surname, name, patronymic = self.get_person_data()
        await self._fill_surname(surname)
        await self._fill_name(name)
        await self._fill_patronymic(patronymic)
        await self.press_btn()


    async def _get_person_data(self):
        """
        Парсинг блока с информацией об управляющем
        """
        await asyncio.sleep(5.5)
        
        fields = {
            "last_name":  "#ctl00_cphBody_trLastName",
            "first_name": "#ctl00_cphBody_trFirstName",
            "middle_name":"#ctl00_cphBody_trMiddleName",
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

    async def get_text_data(self):
        """
        Получение данных о арбитражном управляющем
        """
        await self.press_link("a[title='Карточка арбитражного управляющего']", "fio_person")
        await self._get_person_data()

    
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
            "ur_address_reestr":            "#ctl00_cphBody_trUrAddressReestr",
            "phone":                        "#ctl00_cphBody_trPhone",
            "email":                        "#ctl00_cphBody_trEmail",
            "url":                          "#ctl00_cphBody_trUrl",
            "comp_fund_size_sro":           "#ctl00_cphBody_trCompFundSizeSro",
            "comp_fund_refresh_date_sro":   "#ctl00_cphBody_trCompFundRefreshDateSro",
            "comp_fund_size_reestr":        "#ctl00_cphBody_trCompFundSizeReestr",
            "comp_fund_refresh_date_reestr":"#ctl00_cphBody_trCompFundRefreshDateReestr",
            "first_manager":                "#ctl00_cphBody_trFirstManager",
            "arbitr_managers_count":        "#ctl00_cphBody_trArbitrManagersCount",
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

    def get_person_data(self) -> tuple[str, str, str]:
        """
        :return: tuple[str, str, str] - Фамилия, Имя, Отчество
        """
        name_parts = self.person_name.split(" ")
        return name_parts[0], name_parts[1], name_parts[2]



async def process_parsing(browser, person_name: str):
    """ Запуск парсинга """
    context = await browser.new_context(
        viewport=None,  # Использовать размер экрана по умолчанию (как у обычного браузера)
        # user_agent=ua  # используем рандомный агент
    )
    parser = ParserEFRSB(
        url='https://old.bankrot.fedresurs.ru/ArbitrManagersList.aspx', 
        person_name=person_name
        )
    parser.context = context  # передаем context внутрь парсера
    await parser.run()  # запуск парсера
    await asyncio.sleep(4.6)  # ожидание для завершения всех действий на странице
    await context.close()


async def run_playwright_parsing(person_name: str):
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

            try:
                await process_parsing(browser=browser, person_name=person_name)
            finally:
                # pass для избежания ошибки с Pylance 
                # Python запрещает использовать break, continue или return внутри блока finally в async for
                pass
    finally:
        if browser:
            await browser.close()
