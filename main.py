from src.server import app
from src.core.config import Settings

if __name__ == "__main__":
    import argparse
    import uvicorn

    settings = Settings()

    # Create argument parser
    parser = argparse.ArgumentParser(description="Run Uvicorn server")
    parser.add_argument("--host", type=str, default=settings.host, help="Host to bind")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind")

    # Parse arguments
    args = parser.parse_args()

    # Run Uvicorn with parsed arguments
    uvicorn.run(app, host=args.host, port=args.port)
