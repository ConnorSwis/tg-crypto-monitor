import uvicorn
from tg_crypto_monitor.config import PORT


def main(reload: bool = False):
    """Main function to run the FastAPI app."""
    uvicorn.run("tg_crypto_monitor:app", host="0.0.0.0",
                port=PORT, reload=reload)


main()
