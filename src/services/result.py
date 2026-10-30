"""Interpretação da mensagem final do desafio."""

import re

from src.domain.models import ChallengeResult
from src.exceptions import ChallengeFailedError, RecoverableError

RESULT_PATTERN = re.compile(
    r"(?P<rate>\d+)%.*?(?P<correct>\d+)\s+out of\s+(?P<total>\d+).*?(?P<ms>\d+)\s*milliseconds",
    re.IGNORECASE | re.DOTALL,
)


def parse_result(message: str) -> ChallengeResult:
    """Converte 'Your success rate is 100% ( 70 out of 70 fields) in 812 milliseconds'."""
    match = RESULT_PATTERN.search(message)
    if not match:
        raise RecoverableError(f"Mensagem de resultado inesperada: {message!r}")
    return ChallengeResult(
        success_rate=int(match["rate"]),
        correct_fields=int(match["correct"]),
        total_fields=int(match["total"]),
        elapsed_ms=int(match["ms"]),
        message=" ".join(message.split()),
    )


def ensure_minimum(result: ChallengeResult, minimum_rate: int) -> None:
    """Falha se a taxa de acerto ficou abaixo do mínimo."""
    if result.success_rate < minimum_rate:
        raise ChallengeFailedError(
            f"Taxa de acerto {result.success_rate}% abaixo do mínimo de {minimum_rate}%"
        )
