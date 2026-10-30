import pytest

from src.exceptions import ChallengeFailedError, RecoverableError
from src.services.result import ensure_minimum, parse_result

MESSAGE = "Your success rate is 100% ( 70 out of 70 fields) in 4551 milliseconds"


def test_parses_site_message():
    result = parse_result(MESSAGE)
    assert (result.success_rate, result.correct_fields, result.total_fields) == (100, 70, 70)
    assert result.elapsed_ms == 4551


def test_parses_partial_result_with_line_breaks():
    result = parse_result("Your success rate is 86%\n( 60 out of 70 fields) in 900 milliseconds")
    assert result.success_rate == 86
    assert result.correct_fields == 60


def test_unexpected_message_is_recoverable():
    with pytest.raises(RecoverableError):
        parse_result("Loading...")


@pytest.mark.parametrize(
    ("rate", "minimum", "fails"), [(100, 100, False), (99, 100, True), (80, 80, False)]
)
def test_ensure_minimum(rate, minimum, fails):
    result = parse_result(MESSAGE.replace("100%", f"{rate}%"))
    if fails:
        with pytest.raises(ChallengeFailedError):
            ensure_minimum(result, minimum)
    else:
        ensure_minimum(result, minimum)
