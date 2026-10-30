"""Retentativa com backoff exponencial para operações transitórias."""

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from src.exceptions import RecoverableError, SystemUnavailableError

T = TypeVar("T")
logger = logging.getLogger(__name__)


def with_retry(
    action: Callable[[], T],
    *,
    attempts: int = 3,
    base_wait: float = 2.0,
    retry_on: tuple[type[BaseException], ...] = (RecoverableError, TimeoutError, OSError),
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Executa `action`; em falha transitória espera 2^n segundos e tenta de novo."""
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except retry_on as exc:
            if attempt == attempts:
                raise SystemUnavailableError(f"Falhou após {attempts} tentativas: {exc}") from exc
            wait = base_wait**attempt
            logger.warning(
                "Falha transitória, tentando de novo",
                extra={"attempt": attempt, "wait_seconds": wait, "error": str(exc)},
            )
            sleep(wait)
    raise AssertionError("inalcançável")
