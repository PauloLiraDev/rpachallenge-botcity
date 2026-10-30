"""Log de execução no Maestro: uma linha por Task com os números do desafio."""

import logging
from dataclasses import dataclass

from botcity.maestro import BotMaestroSDK, Column

from src.domain.models import ChallengeResult

logger = logging.getLogger(__name__)


@dataclass
class VisibleColumn(Column):  # type: ignore[misc]
    """O `Column` do SDK não manda `visible`, e o Maestro cria a coluna oculta."""

    visible: bool = True


COLUMNS = [
    VisibleColumn(name="Task", label="task", width=100),
    VisibleColumn(name="Status", label="status", width=90),
    VisibleColumn(name="Acerto (%)", label="rate", width=90),
    VisibleColumn(name="Campos certos", label="fields", width=110),
    VisibleColumn(name="Rodadas", label="rounds", width=80),
    VisibleColumn(name="Tempo no site (ms)", label="challenge_ms", width=130),
    VisibleColumn(name="Duração total (s)", label="duration_s", width=120),
    VisibleColumn(name="Erro", label="error", width=160),
    VisibleColumn(name="Mensagem", label="message", width=380),
]


class ExecutionLog:
    """Grava o resumo da execução; falha no log não derruba a Task."""

    def __init__(self, maestro: BotMaestroSDK, task_id: str | None, label: str) -> None:
        self.maestro = maestro
        self.task_id = str(task_id or "")
        self.label = label

    def write(
        self,
        *,
        rounds: str,
        duration_s: float,
        result: ChallengeResult | None = None,
        error: Exception | None = None,
    ) -> None:
        if not self.task_id:
            return
        row = {
            "task": self.task_id,
            "status": "FALHA" if error else "SUCESSO",
            "rate": str(result.success_rate) if result else "",
            "fields": f"{result.correct_fields}/{result.total_fields}" if result else "",
            "rounds": rounds,
            "challenge_ms": str(result.elapsed_ms) if result else "",
            "duration_s": f"{duration_s:.1f}",
            "error": type(error).__name__ if error else "",
            "message": (str(error) if error else result.message if result else "")[:300],
        }
        try:
            self._send(row)
        except Exception:
            logger.warning("Não foi possível gravar o log de execução", exc_info=True)

    def _send(self, row: dict[str, str]) -> None:
        """Cria o Log na primeira gravação, se ele ainda não existe."""
        try:
            self.maestro.new_log_entry(self.label, row)
        except ValueError:
            self.maestro.new_log(self.label, COLUMNS)
            logger.info("Log de execução criado", extra={"log": self.label})
            self.maestro.new_log_entry(self.label, row)
