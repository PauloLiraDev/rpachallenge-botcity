"""Configuração: parâmetros da Task no Maestro > variáveis de ambiente > padrão."""

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, Field

ENV_PREFIX = "RPA_"


class Settings(BaseModel):
    """Parâmetros de execução do robô."""

    base_url: str = "https://rpachallenge.com/"
    excel_url: str = "https://rpachallenge.com/assets/downloadFiles/challenge.xlsx"
    headless: bool = True
    minimum_success_rate: int = Field(default=100, ge=0, le=100)
    element_timeout_ms: int = Field(default=10_000, gt=0)
    output_dir: Path = Path("output")
    chromedriver_path: str | None = None
    execution_log: str = "rpachallenge-execucoes"

    @classmethod
    def load(cls, task_parameters: Mapping[str, object] | None = None) -> "Settings":
        """Junta ambiente e parâmetros da Task (a Task vence)."""
        values: dict[str, object] = {}
        for name in cls.model_fields:
            env_value = os.getenv(f"{ENV_PREFIX}{name.upper()}")
            if env_value not in (None, ""):
                values[name] = env_value
        for name, value in (task_parameters or {}).items():
            if name in cls.model_fields and value not in (None, ""):
                values[name] = value
        return cls.model_validate(values)
