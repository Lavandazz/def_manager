"""
Запуск парсера ParserKad для получения данных из Картотеки Арбитражных део с использованием playwright.
Парсер открывает главную страницу kad.arbitr.ru
Для получения информации необходимо передавать строку case_number, например А41-16233/2021
"""


import asyncio

from playwright.async_api import async_playwright
from shared.config.db.db_config import get_db
from shared.core.services.parsers.parser_saver_service import ParserDataSaver
from shared.utils.sleep_helper import random_start_sleep
from worker_playwright.parsers.kad_parser import ParserKad
from worker_playwright.utils.dependency import create_parser_data_saver


async def process_parsing(browser, case: str, data_saver: ParserDataSaver):
    """ Запуск парсинга """
    context = await browser.new_context(
        viewport=None,  # Использовать размер экрана по умолчанию (как у обычного браузера)
        # user_agent=ua  # используем рандомный агент
        user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
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
                headless=True,  # True для безголового режима, False для визуального
                channel="chromium",
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
        
