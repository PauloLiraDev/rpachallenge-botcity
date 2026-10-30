"""Criação do WebBot com Chrome, pronto para desktop e contêiner."""

import shutil
from pathlib import Path

from botcity.web import Browser, WebBot
from botcity.web.browsers.chrome import default_options
from selenium.webdriver.common.selenium_manager import SeleniumManager

from src.config import Settings

CONTAINER_ARGS = ("--disable-dev-shm-usage", "--window-size=1366,768")


def resolve_chromedriver(configured: str | None) -> str:
    """Caminho configurado > chromedriver no PATH > Selenium Manager."""
    if configured:
        return configured
    if found := shutil.which("chromedriver"):
        return found
    return str(SeleniumManager().binary_paths(["--browser", "chrome"])["driver_path"])


def build_bot(settings: Settings) -> WebBot:
    """WebBot Chrome com as opções da BotCity e ajustes para Docker."""
    bot = WebBot()
    bot.browser = Browser.CHROME
    bot.headless = settings.headless
    bot.driver_path = resolve_chromedriver(settings.chromedriver_path)
    downloads = Path(settings.output_dir).resolve()
    options = default_options(headless=settings.headless, download_folder_path=str(downloads))
    for arg in CONTAINER_ARGS:
        options.add_argument(arg)
    bot.options = options
    return bot
