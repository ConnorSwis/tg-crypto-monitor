import asyncio
import re
import logging
import traceback
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from telethon import TelegramClient
from telethon import events

from tg_crypto_monitor.config import TG_APP_ID, TG_APP_HASH, TG_PHONE, TG_PASSWORD, MONITORING_IDS, MAX_FEED_SIZE, SESSION_PATH
from tg_crypto_monitor.datatypes.persistent_set import PersistentSet


logger = logging.getLogger()
latest_mint_addresses = PersistentSet("latest_messages.json")
seen_mint_addresses = PersistentSet("seen_mint_addresses.json")
five_digit_code = None
code_event = asyncio.Event()

client = TelegramClient(SESSION_PATH, TG_APP_ID, TG_APP_HASH)
app = FastAPI()
main_app_lifespan = app.router.lifespan_context


@asynccontextmanager
async def lifespan_wrapper(app):
    polling_task = asyncio.create_task(start_telegram_polling())
    try:
        async with main_app_lifespan(app) as maybe_state:
            yield maybe_state
    except Exception as e:
        logger.error(f"Lifespan Exception: {e}")
        raise
    finally:
        polling_task.cancel()


app.router.lifespan_context = lifespan_wrapper


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

        logger.debug(f"WebSocket disconnected: {websocket}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)
                logger.debug(f"WebSocket disconnected: {connection}")


manager = ConnectionManager()


def mint_address_if_exists(message: Optional[str]) -> Optional[str]:
    """Extract a mint address from the message."""
    if not message:
        return None
    mint_address = re.search(r"(?<=💵:)[A-Za-z0-9]+", message)
    if mint_address:
        return mint_address.group(0)
    else:
        base58_pattern = r'[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{44}'
        match = re.search(base58_pattern, message)
        return match.group(0) if match else None


async def code_callback():
    """Asynchronous callback to wait for the code to be set."""
    global five_digit_code
    logging.info("Waiting for code to be set.")
    await code_event.wait()
    return five_digit_code


async def start_telegram_polling():
    """Monitor specified channels, fetching and processing new messages asynchronously."""
    try:
        await client.start(
            phone=(lambda: TG_PHONE),
            password=(lambda: TG_PASSWORD),
            code_callback=code_callback
        )
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await client.disconnect()
        logger.info("Telegram client disconnected.")


@client.on(events.NewMessage(chats=MONITORING_IDS))
async def new_message_handler(event: events.NewMessage.Event):
    """Event handler for new messages."""
    mint_address = mint_address_if_exists(event.message.message)
    if mint_address:
        if not await seen_mint_addresses.contains(mint_address):
            await latest_mint_addresses.add(mint_address)
            await seen_mint_addresses.add(mint_address)
            async with latest_mint_addresses._lock:
                while len(latest_mint_addresses._set) > MAX_FEED_SIZE:
                    oldest = list(latest_mint_addresses._set)[0]
                    await latest_mint_addresses.discard(oldest)
            await manager.broadcast(mint_address)
            logger.info(f"New mint address: {mint_address}")


@app.websocket("/latest/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to emit latest messages."""
    await manager.connect(websocket)
    logger.info("WebSocket connected.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/latest", response_model=List[str])
async def get_latest_messages():
    """FastAPI endpoint to get the latest messages."""
    return await latest_mint_addresses.to_list()


@app.post("/set_code")
async def set_code(code: int):
    """Endpoint to set the 5-digit code."""
    global five_digit_code
    if five_digit_code is not None:
        raise HTTPException(
            status_code=400, detail="Code already set."
        )
    if not (10000 <= code <= 99999):
        raise HTTPException(
            status_code=400, detail="Code must be a 5-digit number."
        )
    five_digit_code = code
    code_event.set()
    return {"message": "Code set successfully."}


@app.get("/health")
async def health():
    return {"status": "ok"}
