FROM modulo-consultas-parlamentarias-core

COPY modulo_consultas_parlamentarias /src/modulo_consultas_parlamentarias
COPY requirements.txt pyproject.toml /src/
RUN --mount=type=bind,target=/root/.cache,source=.git,target=/src/.git \
    uv pip install /src --no-deps

WORKDIR /src
CMD python -m modulo_consultas_parlamentarias.mcp.server
