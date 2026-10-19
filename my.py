
from patchright.async_api import async_playwright
import asyncio

from config.settings_folders import BASE_FOLDER


async def main():

    async with async_playwright() as p:
        # launch Chromium in headless mode
        browser = await p.chromium.launch(
            headless=False,
            args=[
                    "--headless=new",
                    "--start-maximized",  # Окно на весь экран
                    "--disable-blink-features=AutomationControlled",  # Убираем флаг автоматизации
                    "--disable-infobars",  # Убираем сообщение "Chrome is being controlled"
                    "--disable-dev-shm-usage",  # Улучшаем работу в контейнерах
                    "--no-sandbox",  # Полезно в некоторых окружениях
                    "--disable-popup-blocking",
                    "--window-size=1920,1080"
                ],
                chromium_sandbox=False,
                ignore_default_args=["--enable-automation"], )

        page = await browser.new_page()

        # open the target site
        await page.goto("https://old.bankrot.fedresurs.ru/ArbitrManagersList.aspx")
        await asyncio.sleep(5)
        await page.screenshot(path=f"{BASE_FOLDER}/screen/111screenshot.png")
        await browser.close()


asyncio.run(main())