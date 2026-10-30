import pytest

from src.config import Settings
from src.domain.models import Person
from src.exceptions import RecoverableError, SystemUnavailableError
from src.utils.masking import mask_email, mask_phone
from src.utils.retry import with_retry


@pytest.mark.parametrize(
    ("email", "expected"),
    [("jsmith@itsolutions.co.uk", "j***@itsolutions.co.uk"), ("invalido", "***")],
)
def test_mask_email(email, expected):
    assert mask_email(email) == expected


def test_mask_phone():
    assert mask_phone("40716543298") == "***98"
    assert mask_phone("12") == "***"


def test_retry_succeeds_after_transient_failures():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RecoverableError("ainda não")
        return "ok"

    waits: list[float] = []
    assert with_retry(flaky, attempts=3, sleep=waits.append) == "ok"
    assert waits == [2.0, 4.0]


def test_retry_gives_up_as_fatal():
    def always_fails():
        raise RecoverableError("fora do ar")

    with pytest.raises(SystemUnavailableError):
        with_retry(always_fails, attempts=2, sleep=lambda _: None)


def test_phone_float_from_excel_becomes_digits():
    person = Person(
        first_name="a",
        last_name="b",
        company_name="c",
        role="d",
        address="e",
        email="a@b.c",
        phone=40716543298.0,
    )
    assert person.phone == "40716543298"


def test_settings_task_parameters_override_env(monkeypatch):
    monkeypatch.setenv("RPA_HEADLESS", "false")
    monkeypatch.setenv("RPA_MINIMUM_SUCCESS_RATE", "90")
    settings = Settings.load({"minimum_success_rate": "80", "desconhecido": "x"})
    assert settings.headless is False
    assert settings.minimum_success_rate == 80
