#!/usr/bin/env python3
"""
Terminal Interactive Chat App using PydanticAI with MCP Server integration.

This app creates a terminal-based chat interface that connects to an MCP server
and uses Logfire for observability.
The system provides information about both chambers of the Argentine Congress:
the Chamber of Deputies and the Senate.
"""

import asyncio
import os
from pathlib import Path

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.settings import ModelSettings

from cparla.logger import get_logger

# Load environment variables from .env file if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

logger = get_logger(__name__)


class ChatApp:
    """Terminal interactive chat application with MCP server integration for congressional queries."""

    def __init__(
        self,
        mcp_server_url: str = "http://localhost:8000/mcp",
        model: str = "openai:gpt-4o",
        max_tokens: int = 1024,
        temperature: float = 0.0,
        service_name: str = "modulo-consultas-parlamentarias-chat",
    ):
        """Initialize the chat app with configuration."""
        self.mcp_server_url = mcp_server_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.service_name = service_name

        # Check for required environment variables
        self._check_environment()

        # Initialize Logfire
        self._setup_logfire()

        # Initialize MCP server connection
        self.mcp_server = MCPServerStreamableHTTP(mcp_server_url)

        # Initialize the agent
        self.agent = self._create_agent()

        logger.info(f"Chat app initialized with MCP server: {mcp_server_url}")

    def _check_environment(self) -> None:
        """Check for required environment variables and provide helpful error messages."""
        if not os.getenv("OPENAI_API_KEY"):
            print("\n❌ ERROR: OpenAI API key not found!")
            print("Please set your OpenAI API key in one of these ways:")
            print("1. Set environment variable: export OPENAI_API_KEY='your-api-key'")
            print("2. Create a .env file with: OPENAI_API_KEY=your-api-key")
            print("3. Copy .env.example to .env and fill in your API key")
            print("\nYou can get an API key from: https://platform.openai.com/api-keys")
            raise ValueError("OPENAI_API_KEY environment variable is required")

    def _setup_logfire(self) -> None:
        """Set up Logfire instrumentation."""
        try:
            logfire.configure(service_name=self.service_name)
            logfire.instrument_pydantic_ai()
            logfire.instrument_openai()
            logger.info("Logfire instrumentation configured successfully")
        except Exception as e:
            logger.warning(f"Failed to configure Logfire: {e}")

    def _create_agent(self) -> Agent:
        """Create the PydanticAI agent with MCP server toolset."""
        instructions = """
        You are an expert assistant for answering questions about the Argentine Congress (Honorable Congreso de la Nación Argentina).
        
        You have access to tools through the MCP server that allow you to:
        - Query the parliamentary database for both the Chamber of Deputies and the Senate
        - Search for legislators (deputies and senators) and their information
        - Retrieve voting records and statistics from both chambers
        - Access information about parliamentary blocks in both chambers
        - Search for specific parliamentary issues and their details
        
        Search workflow:
        1. For questions about specific legislators, blocks or parliamentary issues, FIRST retrieve their associated metadata including their IDs
        2. Once you have the IDs, use SQL queries to get detailed information from the database
        
        Guidelines:
        - Use the available tools to answer user queries accurately. You can list them calling
        - Do NOT use your own knowledge or speculate about parliamentary data
        - Always respond in Spanish
        - Be helpful and provide clear, detailed answers based on the data
        - If you cannot find specific information, say so clearly
        - When greeting users or introducing yourself, refer to the entire Congress ("Honorable Congreso de la Nación Argentina") and not just one chamber
        """

        return Agent(
            model=self.model,
            instructions=instructions,
            name="Parliamentary Chat Agent",
            model_settings=ModelSettings(
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            ),
            toolsets=[self.mcp_server],
            retries=1,
        )

    def _print_welcome(self) -> None:
        """Print welcome message and instructions."""
        print("\n" + "=" * 60)
        print("🏛️  MÓDULO DE CONSULTAS PARLAMENTARIAS - CHAT INTERACTIVO")
        print("=" * 60)
        print("Bienvenido al asistente de consultas parlamentarias.")
        print("Puedes hacer preguntas sobre:")
        print("  • Votaciones en el Congreso de la Nación")
        print("  • Diputados y Senadores")
        print("  • Estadísticas de votaciones en ambas cámaras")
        print("  • Información sobre bloques políticos")
        print("  • Asuntos parlamentarios")
        print("\nComandos especiales:")
        print("  • 'salir' o 'exit' - Terminar la sesión")
        print("  • 'ayuda' o 'help' - Mostrar esta ayuda")
        print("=" * 60)
        print("Escribe tu consulta y presiona Enter...\n")

    def _print_help(self) -> None:
        """Print help information."""
        print("\n📋 AYUDA - EJEMPLOS DE CONSULTAS")
        print("-" * 40)
        print("• ¿Cuáles fueron los votos de Javier Milei en Diputados?")
        print("• Resumen de votos de [nombre del legislador]")
        print("• ¿Cómo votó el bloque Unión por la Patria en [asunto]?")
        print("• Estadísticas de votación del senador [nombre]")
        print("• ¿Qué asuntos se votaron en [fecha] en el Senado?")
        print("• Comparación de votaciones entre Diputados y Senado sobre [tema]")
        print("-" * 40 + "\n")

    async def _process_user_input(self, user_input: str) -> bool:
        """Process user input and return whether to continue."""
        user_input = user_input.strip()

        # Handle special commands
        if user_input.lower() in ["salir", "exit", "quit"]:
            print(
                "\n👋 ¡Hasta luego! Gracias por usar el Módulo de Consultas Parlamentarias."
            )
            return False

        if user_input.lower() in ["ayuda", "help"]:
            self._print_help()
            return True

        if not user_input:
            print("Por favor, escribe una consulta o 'ayuda' para ver ejemplos.")
            return True

        # Process the query with the agent
        try:
            print("\n🤔 Procesando tu consulta...")

            async with self.agent:
                result = await self.agent.run(user_input)

            print("\n🤖 Respuesta:")
            print("-" * 40)
            print(result.output)
            print("-" * 40)

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"\n❌ Error al procesar la consulta: {e}")
            print("Por favor, intenta con una consulta diferente.")

        return True

    async def run(self) -> None:
        """Run the interactive chat loop."""
        self._print_welcome()

        try:
            while True:
                try:
                    # Get user input
                    user_input = input("💬 Tu consulta: ").strip()

                    # Process input and check if we should continue
                    should_continue = await self._process_user_input(user_input)
                    if not should_continue:
                        break

                    print()  # Add spacing between interactions

                except KeyboardInterrupt:
                    print("\n\n👋 Sesión interrumpida. ¡Hasta luego!")
                    break
                except EOFError:
                    print("\n\n👋 Sesión terminada. ¡Hasta luego!")
                    break

        except Exception as e:
            logger.error(f"Unexpected error in chat loop: {e}")
            print(f"\n❌ Error inesperado: {e}")

        finally:
            logger.info("Chat session ended")


async def main() -> None:
    """Main entry point for the chat application."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Terminal Interactive Chat App for Argentine Congress Queries"
    )
    parser.add_argument(
        "--mcp-url",
        default="http://localhost:8000/mcp",
        help="MCP server URL (default: http://localhost:8000/mcp)",
    )
    parser.add_argument(
        "--model",
        default="openai:gpt-4o",
        help="OpenAI model to use (default: openai:gpt-4o)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for responses (default: 1024)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Model temperature (default: 0.0)",
    )

    args = parser.parse_args()

    # Create and run the chat app
    app = ChatApp(
        mcp_server_url=args.mcp_url,
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
