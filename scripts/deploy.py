"""Deploy no BotCity Orchestrator: bot (.zip) + Runner + Automação, idempotente.

Mesmas rotas que o BotCLI usa (`bot deploy`/`bot release`/`machine new`), via API v2.
Uso: uv run python scripts/deploy.py [--task]
"""

import argparse
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "dist" / "rpachallenge.zip"
TIMEOUT = 60


def load_env(path: Path) -> None:
    """Carrega .env sem sobrescrever variáveis já definidas."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def server_url(server: str) -> str:
    """Mesma regra do wrapper.sh da imagem: 'developers' -> https://developers.botcity.dev."""
    url = server if server.startswith("http") else f"https://{server}"
    return url if "." in url.split("//", 1)[1] else f"{url}.botcity.dev"


class Orchestrator:
    """Cliente mínimo da API v2 do Maestro."""

    def __init__(self, server: str, login: str, key: str) -> None:
        self.base = f"{server_url(server)}/api/v2"
        response = requests.post(
            f"{self.base}/workspace/login", json={"login": login, "key": key}, timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        self.organization = data["organizationLabel"]
        self.session = requests.Session()
        self.session.headers.update(
            {"token": data["accessToken"], "organization": self.organization}
        )

    def get(self, path: str) -> requests.Response:
        return self.session.get(f"{self.base}/{path}", timeout=TIMEOUT)

    def post(self, path: str, **kwargs: object) -> requests.Response:
        return self.session.post(f"{self.base}/{path}", timeout=TIMEOUT, **kwargs)  # type: ignore[arg-type]

    def deploy_bot(self, bot_id: str, version: str, zip_path: Path) -> None:
        payload = {
            "botId": bot_id,
            "version": version,
            "technology": "PYTHON",
            "repositoryLabel": "DEFAULT",
            "organization": self.organization,
        }
        exists = self.get(f"bot/{bot_id}/version/{version}").ok
        if not exists:
            ensure_ok(self.post("bot", json=payload), "criar versão do bot")
        with zip_path.open("rb") as file:
            files = {"file": (zip_path.name, file, "application/zip")}
            ensure_ok(self.post(f"bot/upload/{bot_id}/version/{version}", files=files), "upload")
        ensure_ok(self.post("bot/release", json=payload), "release")
        print(f"bot {bot_id} {version}: {'atualizado' if exists else 'criado'} e liberado")

    def ensure_runner(self, machine_id: str) -> None:
        if self.get(f"machine/{machine_id}").ok:
            print(f"runner {machine_id}: já existe")
            return
        body = {"idMachine": machine_id, "name": machine_id, "type": "DESKTOP"}
        ensure_ok(self.post("machine", json=body), "criar runner")
        print(f"runner {machine_id}: criado")

    def ensure_automation(self, label: str, bot_id: str, machine_id: str) -> None:
        body = {
            "label": label,
            "name": "RPA Challenge - Input Forms",
            "description": "Preenche as 10 rodadas do rpachallenge.com (WebBot, Chrome headless).",
            "agentId": bot_id,
            "technology": "PYTHON",
            "repositoryLabel": "DEFAULT",
            "organizationLabel": self.organization,
            "machines": [machine_id],
            "humanTimePerItem": 60,
        }
        exists = self.get(f"activity/{label}").ok
        response = self.post(f"activity/{label}" if exists else "activity", json=body)
        ensure_ok(response, "salvar automação")
        print(f"automação {label}: {'atualizada' if exists else 'criada'} (runner {machine_id})")

    def create_task(self, label: str) -> None:
        response = self.post("task", json={"activityLabel": label, "parameters": {}})
        ensure_ok(response, "criar task")
        print(f"task {response.json().get('id')} criada para {label}")


def ensure_ok(response: requests.Response, step: str) -> None:
    if not response.ok:
        sys.exit(f"Falha ao {step}: HTTP {response.status_code} {response.text[:300]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", action="store_true", help="cria uma Task depois do deploy")
    args = parser.parse_args()
    load_env(ROOT / ".env")
    if not ZIP.exists():
        sys.exit("dist/rpachallenge.zip não existe: rode scripts/build_zip.py antes")
    bot_id = os.environ.get("BOT_ID", "rpachallenge")
    machine_id = os.environ.get("MACHINE_ID", "rpachallenge-docker")
    orchestrator = Orchestrator(
        os.environ.get("SERVER", "developers"), os.environ["LOGIN"], os.environ["KEY"]
    )
    orchestrator.deploy_bot(bot_id, os.environ.get("BOT_VERSION", "1.0.0"), ZIP)
    orchestrator.ensure_runner(machine_id)
    orchestrator.ensure_automation(bot_id, bot_id, machine_id)
    if args.task:
        orchestrator.create_task(bot_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
