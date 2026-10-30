"""Entrypoint chamado pelo BotCity Runner: resolve o Input Forms do rpachallenge.com."""

import logging
import sys

from botcity.maestro import BotMaestroSDK

from src.browser import build_bot
from src.config import Settings
from src.exceptions import BotError
from src.logging_setup import configure_logging
from src.process import RpaChallengeProcess

BotMaestroSDK.RAISE_NOT_CONNECTED = False
logger = logging.getLogger("bot")


def task_parameters(maestro: BotMaestroSDK) -> dict[str, object]:
    """Parâmetros da Task; vazio quando roda fora do Maestro."""
    if not maestro.task_id:
        return {}
    return dict(maestro.get_execution(maestro.task_id).parameters or {})


def main() -> int:
    configure_logging()
    maestro = BotMaestroSDK.from_sys_args()
    settings = Settings.load(task_parameters(maestro))
    logger.info(
        "Iniciando",
        extra={"task_id": maestro.task_id, "headless": settings.headless},
    )
    bot = build_bot(settings)
    process = RpaChallengeProcess(bot, maestro, settings)
    try:
        result = process.run()
        process.finish_success(result)
        return 0
    except BotError as exc:
        logger.exception("Execução falhou")
        process.finish_failure(exc)
        return 1
    except Exception as exc:
        logger.exception("Erro inesperado")
        process.finish_failure(exc)
        raise
    finally:
        bot.stop_browser()


if __name__ == "__main__":
    sys.exit(main())
