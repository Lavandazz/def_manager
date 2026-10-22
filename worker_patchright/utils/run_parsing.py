"""
Запуск парсера ParserEFRSB из ЕФРСБ портала с использованием patchright.
Парсер открывает страницу ArbitrManagersList для получения данных по арбитражным управляющим.
Для получения данных необходимо передать id пользователя и person_name: строка Иванов Иван Иванович
"""

import asyncio

from patchright.async_api import async_playwright

from ..parsers.efrsb_parser import ParserEFRSB
from shared.config.db.db_config import get_db
from shared.core.services.parsers.parser_sro_service import ParserSroDataSaver
from .dependency import create_parser_sro_data_saver


async def process_efrsb_parsing(browser, person_name: str, user_id: int, data_saver: ParserSroDataSaver):
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
                    await process_efrsb_parsing(browser, person_name, user_id, data_saver)
                finally:
                    # pass для избежания ошибки с Pylance 
                    # Python запрещает использовать break, continue или return внутри блока finally в async for
                    pass
                break   # выполняется после finally и закрывает соединение

    finally:
        if browser:
            await browser.close()
