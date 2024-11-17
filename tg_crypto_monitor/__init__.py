import re
import asyncio
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from telethon import TelegramClient, events
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from tg_crypto_monitor.datatypes.persistent_set import PersistentSet
from tg_crypto_monitor.config import config


@asynccontextmanager
async def lifespan_wrapper(app: FastAPI):
    try:
        asyncio.create_task(client.start(
            phone=(lambda: config.telegram.phone),
            password=(lambda: config.telegram.password),
            code_callback=code_callback
        ))
        await seen_mint_addresses.load()
        async with main_app_lifespan(app) as maybe_state:
            yield maybe_state
    except Exception as e:
        logger.error(f"Lifespan Exception: {e}")
        raise
    finally:
        await client.disconnect()
        logger.info("Telegram client disconnected.")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        logger.debug(f"WebSocket connected: {websocket}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

        logger.debug(f"WebSocket disconnected: {websocket}")

    async def broadcast(self, message: str):
        logger.debug(f"Broadcasting message: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)
                logger.debug(f"WebSocket disconnected: {connection}")


logger = logging.getLogger()
manager = ConnectionManager()
seen_mint_addresses = PersistentSet(
    config.save_dir / "seen_mint_addresses.json"
)
five_digit_code = None
code_event = asyncio.Event()
client = TelegramClient(
    config.telegram.session_file,
    config.telegram.app_id,
    config.telegram.app_hash
)
app = FastAPI()
main_app_lifespan = app.router.lifespan_context
app.router.lifespan_context = lifespan_wrapper


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


@client.on(events.NewMessage(chats=config.telegram.monitoring_ids))
async def new_message_handler(event: events.NewMessage.Event):
    """Event handler for new messages."""
    mint_address = mint_address_if_exists(event.message.message)
    if mint_address:
        if not await seen_mint_addresses.contains(mint_address):
            await seen_mint_addresses.add(mint_address)
            await manager.broadcast(mint_address)
            logger.info(f"Found new mint address: {mint_address}")


@app.websocket("/latest")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to emit latest messages."""
    await manager.connect(websocket)
    logger.info("WebSocket connected.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
