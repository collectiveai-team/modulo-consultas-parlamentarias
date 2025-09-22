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
