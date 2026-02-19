"""
ACW Server — Entry Point

Usage:
    # Start the server
    python -m server.server

    # Or with custom host/port
    python -m server.server --host 0.0.0.0 --port 8080
"""

import argparse
import uvicorn

from . import config


def main():
    parser = argparse.ArgumentParser(description="ACW Server")
    parser.add_argument("--host", default=config.HOST, help="Bind host")
    parser.add_argument("--port", type=int, default=config.PORT, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    uvicorn.run(
        "server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
