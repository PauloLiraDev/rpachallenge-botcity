"""Page Object do Input Forms do rpachallenge.com."""

from typing import Any, ClassVar

from botcity.web import By, WebBot

from src.domain.models import Person
from src.exceptions import RecoverableError


class ChallengePage:
    """Os campos trocam de lugar a cada rodada; `ng-reflect-name` é o que não muda."""

    START_BUTTON = "//button[normalize-space()='Start']"
    SUBMIT_BUTTON = "input[type='submit'][value='Submit']"
    RESULT_MESSAGE = ".message2"
    FIELD_SELECTOR = "input[ng-reflect-name='{name}']"
    FIELDS: ClassVar[dict[str, str]] = {
        "labelFirstName": "first_name",
        "labelLastName": "last_name",
        "labelCompanyName": "company_name",
        "labelRole": "role",
        "labelAddress": "address",
        "labelEmail": "email",
        "labelPhone": "phone",
    }

    def __init__(self, bot: WebBot, timeout_ms: int) -> None:
        self.bot = bot
        self.timeout_ms = timeout_ms

    def open(self, url: str) -> None:
        self.bot.browse(url)
        self._find(self.START_BUTTON, By.XPATH)

    def start(self) -> None:
        self._find(self.START_BUTTON, By.XPATH).click()

    def fill(self, person: Person) -> None:
        for name, attribute in self.FIELDS.items():
            element = self._find(self.FIELD_SELECTOR.format(name=name))
            element.clear()
            element.send_keys(getattr(person, attribute))

    def submit(self) -> None:
        self._find(self.SUBMIT_BUTTON).click()

    def result_message(self) -> str:
        return str(self._find(self.RESULT_MESSAGE).text)

    def _find(self, selector: str, by: str = By.CSS_SELECTOR) -> Any:
        element = self.bot.find_element(selector, by, waiting_time=self.timeout_ms)
        if element is None:
            raise RecoverableError(f"Elemento não encontrado: {selector}")
        return element
