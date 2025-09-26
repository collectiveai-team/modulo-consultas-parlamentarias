# Módulo de Consultas Parlamentarias

A comprehensive system for managing and querying parliamentary data using SQLModel, Qdrant vector database, and MCP (Model Context Protocol) server.

## Features

- **Database Management**: SQLModel-based database system with Alembic migrations
- **Vector Search**: Qdrant integration for semantic search capabilities  
- **MCP Server**: Model Context Protocol server for AI assistant integration
- **Interactive Chat App**: Terminal-based chat interface with PydanticAI integration
- **Parliamentary Data**: Models for managing deputies, political blocks, issues, and voting records
- **CSV Data Import**: Automated population from CSV files with proper encoding handling
- **Logfire Integration**: Comprehensive observability and monitoring

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- uv (for package management)

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd modulo-consultas-parlamentarias

# Install dependencies with uv
uv sync

# Create environment file (copy from example if available)
cp .env.example .env  # Edit with your configuration

# Download prepared database tables
make download-tables
```

### 2. Database Setup

Start by running the database migrations and populating with initial data:

```bash
# Initialize database and run migrations
make db-migrate

# Create database tables
make db-create-tables

# If you downloaded tables data with the download-tables command,
# the data is already available in resources/data/tables/

# Populate database with CSV data
make db-populate
```

### 3. Start Vector Database (Qdrant)

```bash
# Start Qdrant service
make qdrant-start

# Verify Qdrant is running (should be available at http://localhost:6333)

# Create vector collections for search functionality
make create-collections
```

### 4. Run the MCP Server

```bash
# Run MCP server
uv run python cparla/server/server.py
```

### 5. Environment Configuration

Set up your environment variables for the chat application:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_openai_api_key_here
```

**Required Environment Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key (get one from https://platform.openai.com/api-keys)

**Optional Environment Variables:**
- `LOGFIRE_TOKEN`: For Logfire observability (run `logfire auth` to set up)

### 6. Interactive Chat Application

Start the terminal-based chat interface to interact with the parliamentary data:

```bash
# Start the interactive chat app
uv run chat-app

# Or with custom MCP server URL
uv run chat-app --mcp-url http://localhost:8000/mcp

# Or with different model settings
uv run chat-app --model openai:gpt-4o --temperature 0.1 --max-tokens 2048
```

The chat app provides an interactive terminal interface where you can ask questions like:
- "¿Cuáles fueron los votos de Javier Milei?"
- "Resumen de votos de Myriam Bregman"
- "¿Cómo votó el bloque Unión por la Patria en la Ley de Bases?"

### 7. Development Server

For development, you can run the core application:

```bash
# Build and run core application
make core-run
```

## Available Make Commands

### Database Operations
- `make db-init` - Initialize database
- `make db-create-tables` - Create database tables
- `make db-migrate` - Run Alembic migrations
- `make db-populate` - Populate database from CSV files
- `make db-migration MESSAGE="description"` - Create new migration
- `make db-example` - Run database usage example
- `make create-collections` - Create Qdrant vector collections for parliamentary data
- `make create-collections-force` - Recreate Qdrant collections (deletes existing ones)

### Qdrant Operations
- `make qdrant-start` - Start Qdrant vector database
- `make qdrant-stop` - Stop Qdrant service
- `make qdrant-restart` - Restart Qdrant service
- `make qdrant-flush` - Delete all Qdrant data (WARNING: destructive)

### MCP Server Operations
- `make mcp-build` - Build MCP server image
- `make mcp-run` - Run MCP server interactively
- `make mcp-up` - Start MCP server as daemon
- `make mcp-stop` - Stop MCP server
- `make mcp-restart` - Restart MCP server

### Development
- `make core-build` - Build core application
- `make core-run` - Run core application
- `make linter` - Run code linting and formatting
- `make linter-fix` - Run linting with auto-fix

### Chat Application
- `uv run chat-app` - Start interactive chat application
- `uv run chat-app --help` - Show chat app options

## Database Models

The system includes the following main models:

- **DBAsuntoDiputado**: Parliamentary issues/matters
- **DBBloqueDiputado**: Political blocks/parties  
- **DBLegisladorDiputado**: Deputies/legislators
- **DBVotacionDiputado**: Parliamentary votes

Each model has corresponding public versions for API interfaces.

## MCP Server Features

The MCP server provides:

- **Database Resources**: Access to table schemas and data previews
- **SQL Query Tool**: Safe SELECT query execution with limits
- **Table Listing**: Browse available tables and their metadata

### MCP Resources

- `db://tables` - List all available tables
- `db://schema/{table_name}` - Get detailed table schema
- `db://preview/{table_name}?limit=N` - Preview table data

### MCP Tools

- `run_select(sql_query, limit)` - Execute SELECT queries safely

## Interactive Chat Application

The chat application provides a terminal-based interface for querying parliamentary data using natural language. It integrates PydanticAI with the MCP server and includes Logfire observability.

### Features

- **Natural Language Queries**: Ask questions in Spanish about parliamentary data
- **MCP Integration**: Connects to the MCP server for data access
- **Logfire Observability**: Full tracing and monitoring of AI interactions
- **Error Handling**: Graceful error handling with helpful messages
- **Command Support**: Built-in help and exit commands

### Usage Examples

```bash
# Basic usage
uv run chat-app

# Custom configuration
uv run chat-app --mcp-url http://localhost:8000/mcp --model openai:gpt-4o

# Show help
uv run chat-app --help
```

### Example Queries

- "¿Cuáles fueron los votos de Javier Milei?"
- "Resumen de votos de Myriam Bregman, desglosando afirmativos, negativos y abstenciones"
- "¿Cómo votó el bloque Unión por la Patria en la Ley de Bases?"
- "¿Qué asuntos se votaron en febrero de 2024?"
- "Estadísticas de votación del diputado José Luis Espert"

### Configuration Options

- `--mcp-url`: MCP server URL (default: http://localhost:8000/mcp)
- `--model`: OpenAI model to use (default: openai:gpt-4o)
- `--max-tokens`: Maximum response tokens (default: 1024)
- `--temperature`: Model temperature (default: 0.0)

### Programmatic Usage

```python
from cparla.chat_app import ChatApp
import asyncio

async def example():
    app = ChatApp(mcp_server_url="http://localhost:8000/mcp")
    
    async with app.agent:
        result = await app.agent.run("¿Cuáles fueron los votos de Javier Milei?")
        print(result.output)

asyncio.run(example())
```

## Project Structure

```
cparla/
├── db/                     # Database models and services
│   ├── models/            # SQLModel definitions
│   ├── services.py        # Service layer
│   ├── engine.py          # Database engine
│   └── populate.py        # CSV data loading
├── server/                # MCP server implementation
├── retriever/             # Vector search functionality
├── logger/                # Logging utilities
└── chat_app.py            # Interactive chat application

scripts/
├── chat_cli.py            # CLI entry point for chat app
├── populate_db.py         # Database population script
└── db_manager.py          # Database management utilities

docker/
├── core/                  # Core application Docker
└── mcp/                   # MCP server Docker

examples/
└── chat_app_example.py    # Chat app usage examples

notebooks/                 # Jupyter notebooks for development
resources/                 # Data and configuration files
alembic/                   # Database migrations
```

## Troubleshooting

### Database Issues
- Ensure database migrations are up to date: `make db-migrate`
- Check if tables exist: `make db-create-tables`
- Verify CSV data loading: `make db-populate`

### Qdrant Issues  
- Check if Qdrant is running: `docker ps | grep qdrant`
- Restart Qdrant: `make qdrant-restart`
- Check logs: `docker logs modulo-consultas-parlamentarias-qdrant`

### MCP Server Issues
- Check server logs: `docker logs modulo-consultas-parlamentarias-mcp`
- Rebuild and restart: `make mcp-restart`
- Run interactively for debugging: `make mcp-run`

## Contributing

1. Follow PEP8 style guidelines
2. Use type hints consistently
3. Run linting before committing: `make linter`
4. Write tests for new functionality
5. Update documentation as needed
