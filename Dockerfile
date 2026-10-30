# Imagem oficial da BotCity: Debian + Java + BotRunner/BotCLI + Chrome/chromedriver + Python 3.11.
# Não sobrescreva ENTRYPOINT/CMD no estágio `runner`: o wrapper.sh da BotCity depende deles.
ARG BOTCITY_IMAGE=botcity/botcity-python-web-chrome:v3.6.0.1

FROM ${BOTCITY_IMAGE} AS base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_FIND_LINKS=/botcity/wheels
COPY requirements.txt /tmp/requirements.txt
# Wheelhouse: o Runner cria um venv por bot e roda `pip install -r requirements.txt`;
# com PIP_FIND_LINKS a instalação usa estas wheels e não depende da rede.
RUN python3.11 -m venv /tmp/pip \
    && /tmp/pip/bin/pip install --no-cache-dir --upgrade pip wheel \
    && /tmp/pip/bin/pip wheel --no-cache-dir -r /tmp/requirements.txt -w /botcity/wheels \
    && rm -rf /tmp/pip

# Executa o bot direto no contêiner, sem Maestro (smoke test da imagem).
FROM base AS local
WORKDIR /app
RUN python3.11 -m venv /opt/venv && /opt/venv/bin/pip install --no-index -r /tmp/requirements.txt
COPY bot.py ./
COPY src ./src
ENV RPA_HEADLESS=true RPA_OUTPUT_DIR=/app/output
ENTRYPOINT ["/opt/venv/bin/python", "bot.py"]

# Padrão: BotCity Runner, que busca Tasks no Maestro e baixa o bot publicado.
FROM base AS runner
