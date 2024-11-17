from dotenv import load_dotenv
import os
import logging
import sys
from pathlib import Path


load_dotenv()

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdout_handler.setFormatter(formatter)
_logger = logging.getLogger()
_logger.setLevel(logging.INFO)
_logger.addHandler(stdout_handler)

constants = {
    # * means required
    "TG_APP_ID": "* The id of the Telegram API",
    "TG_APP_HASH": "* The hash of the Telegram API",
    "TG_PHONE": "* The password of the Telegram account",
    "TG_PASSWORD": "* The phone number of the Telegram account",
    "MONITORING_IDS": "* The ids of the channels to monitor separated by commas",
    "SESSION_DIRECTORY": "The local directory to store the session file.",
    "MAX_FEED_SIZE": "The maximum number of messages to store in the database",
    "PORT": "The local port to run the FastAPI app"
}

TG_APP_ID = os.getenv("TG_APP_ID")
if TG_APP_ID is None:
    raise ValueError("TG_APP_ID not found in environment")
try:
    TG_APP_ID = int(TG_APP_ID)
except ValueError:
    raise ValueError("TG_APP_ID must be an integer")


TG_APP_HASH = os.getenv("TG_APP_HASH")
if TG_APP_HASH is None:
    raise ValueError("TG_APP_HASH not found in environment")


TG_PHONE = os.getenv("TG_PHONE")
if TG_PHONE is None:
    raise ValueError("TG_PHONE not found in environment")


TG_PASSWORD = os.getenv("TG_PASSWORD")
if TG_PASSWORD is None:
    raise ValueError("TG_PASSWORD not found in environment")

_session_directory = os.getenv("SESSION_DIRECTORY")
if not _session_directory:
    _session_directory = Path.cwd() / "session"
else:
    _session_directory = Path(_session_directory).expanduser().resolve()
if not _session_directory.exists():
    _session_directory.mkdir(parents=True, exist_ok=True)
if not _session_directory.is_dir():
    raise ValueError(
        f"The path '{_session_directory}' exists but is not a directory."
    )
SESSION_PATH = _session_directory / "telegram_monitoring.session"


MONITORING_IDS = os.getenv("MONITORING_IDS")
if MONITORING_IDS is None:
    raise ValueError("MONITORING_IDS not found in environment")
else:
    try:
        MONITORING_IDS = [int(id)
                          for id in MONITORING_IDS.replace(" ", "").split(",")]
    except ValueError:
        raise ValueError(
            "MONITORING_IDS must be a comma-separated list of integers")


MAX_FEED_SIZE = os.getenv("MAX_FEED_SIZE")
if MAX_FEED_SIZE is None:
    MAX_FEED_SIZE = 10
else:
    try:
        MAX_FEED_SIZE = int(MAX_FEED_SIZE)
    except ValueError:
        raise ValueError("MAX_FEED_SIZE must be an integer")


PORT = os.getenv("PORT")
if not PORT:
    PORT = 8000
else:
    try:
        PORT = int(PORT)
    except ValueError:
        raise ValueError("PORT must be an integer.")
