# rpachallenge-botcity

Robô BotCity (Python, `WebBot` + Chrome headless) que resolve o **Input Forms** do
[rpachallenge.com](https://rpachallenge.com): baixa `challenge.xlsx`, clica em *Start* e preenche
as 10 rodadas. Os campos mudam de lugar a cada rodada; o robô localiza cada um pelo atributo
`ng-reflect-name`, que não muda. Resultado local: **100% (70/70 campos) em ~4,5 s**.

## Estrutura

| Caminho | O quê |
|---|---|
| `bot.py` | Entrypoint do Runner: Maestro, configuração, tratamento de erro |
| `src/process.py` | Fluxo do desafio e reporte ao Maestro (finish, artifacts, error, alert) |
| `src/pages/challenge_page.py` | Page Object (seletores e cliques) |
| `src/services/` | Download, leitura da planilha e leitura do resultado (sem driver) |
| `src/domain/models.py` | `Person` e `ChallengeResult` (Pydantic) |
| `src/browser.py` | `WebBot` Chrome com as opções da BotCity + ajustes para contêiner |
| `scripts/build_zip.py` | Regenera `requirements.txt` (uv export, sem dev) e gera `dist/rpachallenge.zip` |
| `scripts/deploy.py` | Publica bot, Runner e Automação no Maestro (idempotente) |
| `Dockerfile` / `docker-compose.yml` | Runner da BotCity em Docker, smoke test local e deploy |

## Parâmetros

Ordem de precedência: parâmetro da Task no Maestro > variável `RPA_*` > padrão.

| Parâmetro | Padrão | |
|---|---|---|
| `headless` | `true` | Chrome sem janela |
| `minimum_success_rate` | `100` | Abaixo disso a Task termina como FAILED |
| `element_timeout_ms` | `10000` | Espera por elemento |
| `base_url` / `excel_url` | rpachallenge.com | |

## Rodar localmente

```bash
uv sync
uv run python bot.py                  # sem Maestro (modo offline)
RPA_HEADLESS=false uv run python bot.py
uv run pytest && uv run ruff check . && uv run mypy src bot.py
```

Saída em `output/`: `resultado.json`, `resultado.png` (ou `erro.png`).

## Deploy no BotCity

Credenciais em `.env` (copie de `.env.example`; valores da página *Dev. Environment*).

```bash
uv run python scripts/build_zip.py    # requirements.txt + dist/rpachallenge.zip
uv run python scripts/deploy.py       # bot + Runner (DESKTOP) + Automação "rpachallenge"
uv run python scripts/deploy.py --task  # idem e já cria uma Task
```

Nova versão: suba `BOT_VERSION` no `.env`, rode os dois comandos de novo.

### Com Docker

A imagem parte de `botcity/botcity-python-web-chrome` (Debian, Python 3.11, Chrome + chromedriver,
BotRunner). O estágio `base` pré-compila as dependências em `/botcity/wheels`, e `PIP_FIND_LINKS`
faz o `pip install` do Runner usar essas wheels.

```bash
docker compose build runner local
docker compose run --rm local         # smoke test: roda o bot no contêiner, sem Maestro
docker compose run --rm deploy        # mesmo deploy, de dentro da imagem
docker compose up -d runner           # Runner "rpachallenge-docker" ouvindo o Maestro
```

Com o Runner ativo, crie uma Task da Automação **rpachallenge** no Maestro (ou
`scripts/deploy.py --task`). Chrome no contêiner precisa de `shm_size: 1gb` (já no compose).

## Notas

- `setuptools` é dependência de runtime: o `undetected-chromedriver` (dependência do
  `botcity-framework-web`) ainda importa `distutils`, que não existe no Python 3.12+.
- O plano Community não permite Runner do tipo BACKGROUND; o deploy cria um DESKTOP.
- Os prints enviados ao Maestro são da planilha do desafio (dados fictícios), sem PII real.
