from dataclasses import asdict

from src.domain.models import ChallengeResult
from src.exceptions import ChallengeFailedError
from src.execution_log import COLUMNS, ExecutionLog

RESULT = ChallengeResult(
    success_rate=100,
    correct_fields=70,
    total_fields=70,
    elapsed_ms=6112,
    message="Your success rate is 100% ( 70 out of 70 fields) in 6112 milliseconds",
)


class FakeMaestro:
    def __init__(self, log_exists=True, fail=False):
        self.log_exists = log_exists
        self.fail = fail
        self.entries = []
        self.created = []

    def new_log(self, label, columns):
        self.created.append((label, columns))
        self.log_exists = True

    def new_log_entry(self, label, values):
        if self.fail:
            raise RuntimeError("fora do ar")
        if not self.log_exists:
            raise ValueError("Log not found.")
        self.entries.append((label, values))


def test_success_row():
    maestro = FakeMaestro()
    ExecutionLog(maestro, 42, "execucoes").write(rounds="10/10", duration_s=8.04, result=RESULT)
    assert maestro.entries == [
        (
            "execucoes",
            {
                "task": "42",
                "status": "SUCESSO",
                "rate": "100",
                "fields": "70/70",
                "rounds": "10/10",
                "challenge_ms": "6112",
                "duration_s": "8.0",
                "error": "",
                "message": RESULT.message,
            },
        )
    ]


def test_failure_row_keeps_partial_numbers():
    maestro = FakeMaestro()
    error = ChallengeFailedError("Taxa de acerto 90% abaixo do mínimo de 100%")
    ExecutionLog(maestro, 42, "execucoes").write(rounds="3/10", duration_s=2.0, error=error)
    row = maestro.entries[0][1]
    assert row["status"] == "FALHA"
    assert row["rounds"] == "3/10"
    assert row["rate"] == ""
    assert row["error"] == "ChallengeFailedError"
    assert row["message"] == str(error)


def test_creates_log_with_visible_columns_when_missing():
    maestro = FakeMaestro(log_exists=False)
    ExecutionLog(maestro, 42, "execucoes").write(rounds="10/10", duration_s=1, result=RESULT)
    assert maestro.created == [("execucoes", COLUMNS)]
    assert all(asdict(column)["visible"] for column in COLUMNS)
    assert len(maestro.entries) == 1


def test_offline_sends_nothing():
    maestro = FakeMaestro()
    ExecutionLog(maestro, None, "execucoes").write(rounds="10/10", duration_s=1, result=RESULT)
    assert maestro.entries == []


def test_maestro_errors_do_not_raise():
    maestro = FakeMaestro(fail=True)
    ExecutionLog(maestro, 42, "execucoes").write(rounds="10/10", duration_s=1, result=RESULT)
    assert maestro.entries == []
