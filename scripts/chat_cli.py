#!/usr/bin/env python3
"""
CLI entry point for the Parliamentary Chat App.

This script provides a command-line interface to start the interactive
chat application for parliamentary queries.
"""

import asyncio
import sys

from cparla.chat_app import main


def cli_main() -> None:
    """CLI entry point that runs the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Chat application interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting chat application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
