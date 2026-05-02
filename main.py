"""
BioOracle - ReAct Based Agent for Autonomous Medical Literature Dashboard Generation
Entry point for the application.
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main():
    """Start the BioOracle application."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENV", "development") == "development"

    print("Starting BioOracle server...")
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
