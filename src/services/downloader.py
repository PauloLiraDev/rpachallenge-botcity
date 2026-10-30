"""Download da planilha do desafio."""

import logging
import urllib.request
from pathlib import Path

from src.exceptions import RecoverableError
from src.utils.retry import with_retry

logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 30
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) rpachallenge-botcity/1.0"


def _fetch(url: str, destination: Path) -> Path:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            destination.write_bytes(response.read())
    except OSError as exc:
        raise RecoverableError(f"Download falhou: {exc}") from exc
    if destination.stat().st_size == 0:
        raise RecoverableError("Planilha baixada está vazia")
    return destination


def download_spreadsheet(url: str, output_dir: Path) -> Path:
    """Baixa a planilha com retentativa e devolve o caminho local."""
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "challenge.xlsx"
    path = with_retry(lambda: _fetch(url, destination))
    logger.info("Planilha baixada", extra={"path": str(path), "bytes": path.stat().st_size})
    return path
