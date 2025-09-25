.PHONY: core-build devcontainer-build


core-build:
	docker compose build modulo-consultas-parlamentarias-core

core-run:
	docker compose run modulo-consultas-parlamentarias-core


devcontainer-build: core-build
	docker compose -f .devcontainer/docker-compose.yml build modulo-consultas-parlamentarias-devcontainer


qdrant-start:
	docker compose up -d modulo-consultas-parlamentarias-qdrant

qdrant-stop:
	docker compose stop modulo-consultas-parlamentarias-qdrant

qdrant-restart: qdrant-stop qdrant-start

qdrant-flush: qdrant-stop
	sudo rm -r ./resources/db/qdrant
	$(info *** WARNING you are deleting all data from qdrant ***)
	docker compose up -d modulo-consultas-parlamentarias-qdrant


mcp-build:
	docker compose build modulo-consultas-parlamentarias-mcp

mcp-run: mcp-build
	docker compose  run --rm modulo-consultas-parlamentarias-mcp

mcp-up: mcp-build
	docker compose up -d modulo-consultas-parlamentarias-mcp

mcp-stop:
	docker stop modulo-consultas-parlamentarias-mcp

mcp-restart: mcp-stop mcp-up


# Database operations
db-init:
	uv run python -m scripts.db_manager init

db-create-tables:
	uv run python -m scripts.db_manager create-tables

db-populate:
	uv run python -m scripts.populate_db

download-tables:
	uv run python -m scripts.download_tables
	
create-collections:
	uv run python -m scripts.create_collections

create-collections-force:
	uv run python -m scripts.create_collections --force

db-migrate:
	uv run alembic -c modulo_consultas_parlamentarias/alembic.ini upgrade head

db-migration:
	uv run alembic -c modulo_consultas_parlamentarias/alembic.ini revision --autogenerate -m "$(MESSAGE)"

# Linting and formatting
linter:
	uv run ruff check ./
	uv run ruff format ./

linter-fix:
	uv run ruff check --fix ./
	uv run ruff format ./
	
# Server operations
server-run:
    uv run python -m modulo_consultas_parlamentarias.server.server
