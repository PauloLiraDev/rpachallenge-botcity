"""Fluxo do desafio e reporte ao Maestro."""

import json
import logging
import time
from pathlib import Path

from botcity.maestro import AlertType, AutomationTaskFinishStatus, BotMaestroSDK
from botcity.web import WebBot

from src.config import Settings
from src.domain.models import ChallengeResult, Person
from src.execution_log import ExecutionLog
from src.pages.challenge_page import ChallengePage
from src.services.downloader import download_spreadsheet
from src.services.result import ensure_minimum, parse_result
from src.services.spreadsheet import read_people
from src.utils.masking import mask_email
from src.utils.retry import with_retry

logger = logging.getLogger(__name__)


class RpaChallengeProcess:
    """Baixa a planilha, preenche as 10 rodadas e publica o resultado."""

    def __init__(self, bot: WebBot, maestro: BotMaestroSDK, settings: Settings) -> None:
        self.bot = bot
        self.maestro = maestro
        self.settings = settings
        self.task_id = maestro.task_id
        self.output_dir = Path(settings.output_dir)
        self.page = ChallengePage(bot, settings.element_timeout_ms)
        self.execution_log = ExecutionLog(maestro, self.task_id, settings.execution_log)
        self.started = time.monotonic()
        self.result: ChallengeResult | None = None
        self.people: list[Person] = []
        self.submitted = 0

    def run(self) -> ChallengeResult:
        spreadsheet = download_spreadsheet(self.settings.excel_url, self.output_dir)
        self.people = read_people(spreadsheet)
        logger.info("Planilha lida", extra={"rows": len(self.people)})
        self.bot.start_browser()
        with_retry(lambda: self.page.open(self.settings.base_url))
        self.page.start()
        for round_number, person in enumerate(self.people, start=1):
            self._submit_round(round_number, person)
        result = with_retry(lambda: parse_result(self.page.result_message()), attempts=2)
        self.result = result
        self._publish(result)
        ensure_minimum(result, self.settings.minimum_success_rate)
        return result

    def finish_success(self, result: ChallengeResult) -> None:
        self.execution_log.write(rounds=self._rounds(), duration_s=self._elapsed(), result=result)
        self.maestro.finish_task(
            task_id=self.task_id,
            status=AutomationTaskFinishStatus.SUCCESS,
            message=result.message,
            total_items=len(self.people),
            processed_items=self.submitted,
            failed_items=0,
        )

    def finish_failure(self, error: Exception) -> None:
        self.execution_log.write(
            rounds=self._rounds(), duration_s=self._elapsed(), result=self.result, error=error
        )
        screenshot = self._screenshot("erro.png")
        self.maestro.error(task_id=self.task_id, exception=error, screenshot=screenshot)
        self.maestro.alert(
            task_id=self.task_id,
            title="RPA Challenge falhou",
            message=str(error),
            alert_type=AlertType.ERROR,
        )
        self.maestro.finish_task(
            task_id=self.task_id,
            status=AutomationTaskFinishStatus.FAILED,
            message=str(error),
            total_items=len(self.people),
            processed_items=self.submitted,
            failed_items=len(self.people) - self.submitted,
        )

    def _submit_round(self, round_number: int, person: Person) -> None:
        self.page.fill(person)
        self.page.submit()
        self.submitted += 1
        logger.info(
            "Rodada enviada",
            extra={"round": round_number, "email": mask_email(person.email)},
        )

    def _publish(self, result: ChallengeResult) -> None:
        logger.info("Desafio concluído", extra=result.model_dump(exclude={"message"}))
        report = self.output_dir / "resultado.json"
        report.write_text(json.dumps(result.model_dump(), indent=2), encoding="utf-8")
        self.maestro.post_artifact(self.task_id, "resultado.json", str(report))
        # Dados da planilha são fictícios (vêm do próprio desafio): o print não tem PII real.
        if screenshot := self._screenshot("resultado.png"):
            self.maestro.post_artifact(self.task_id, "resultado.png", screenshot)

    def _rounds(self) -> str:
        return f"{self.submitted}/{len(self.people)}"

    def _elapsed(self) -> float:
        return time.monotonic() - self.started

    def _screenshot(self, name: str) -> str | None:
        if self.bot.driver is None:
            return None
        path = self.output_dir / name
        self.bot.save_screenshot(str(path))
        return str(path)
