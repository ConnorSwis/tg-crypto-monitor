import asyncio
import random
import re
import logging
import traceback
from contextlib import asynccontextmanager
from typing import List, Callable, Coroutine, Optional

from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.functions.messages import GetDialogsRequest, GetHistoryRequest
from telethon.tl.types import Channel, InputPeerEmpty

from tg_crypto_monitor.config import TG_APP_ID, TG_APP_HASH, TG_PHONE, TG_PASSWORD, MONITORING_IDS, LIMIT_MSG, MAX_FEED_SIZE, SESSION_PATH
from tg_crypto_monitor.datatypes.persistent_set import PersistentSet

logger = logging.getLogger()

latest_mint_addresses = PersistentSet("latest_messages.json")
seen_mint_addresses = PersistentSet("seen_mint_addresses.json")
five_digit_code = None
code_event = asyncio.Event()


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


async def fetch_target_groups(*, client: TelegramClient, semaphore: asyncio.Semaphore
                              ) -> List[Channel]:
    """Fetch group chats from the client and filter to include only target channels."""
    try:
        async with semaphore:
            result = await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=100000,
                hash=0
            ))
        return [chat for chat in result.chats if chat.id in MONITORING_IDS]
    except RPCError as e:
        logger.error(f"Error fetching target groups: {e}")
        return []


async def fetch_messages(channel_entity, *, client: TelegramClient, semaphore: asyncio.Semaphore):
    """Fetch recent messages from a given channel entity."""
    try:
        async with semaphore:
            posts = await client(GetHistoryRequest(
                peer=channel_entity,
                limit=LIMIT_MSG,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
        return posts.messages
    except RPCError as e:
        logger.error(f"Error fetching messages for {channel_entity.id}: {e}")
        return []


async def process_messages(messages, on_change: Optional[Callable | Coroutine] = None):
    """Process each new message and update the PersistentSet."""
    for message in messages:
        mint_address = mint_address_if_exists(message.message)
        if mint_address:
            if not await seen_mint_addresses.contains(mint_address):
                await latest_mint_addresses.add(mint_address)
                await seen_mint_addresses.add(mint_address)
                async with latest_mint_addresses._lock:
                    while len(latest_mint_addresses._set) > MAX_FEED_SIZE:
                        oldest = list(latest_mint_addresses._set)[0]
                        await latest_mint_addresses.discard(oldest)

                if on_change is not None:
                    if asyncio.iscoroutinefunction(on_change):
                        await on_change(mint_address)
                    else:
                        on_change(mint_address)


async def code_callback():
    """Asynchronous callback to wait for the code to be set."""
    global five_digit_code
    logging.info("Waiting for code to be set.")
    await code_event.wait()
    return five_digit_code


async def monitor_channels(on_change: Optional[Callable | Coroutine] = None):
    """Monitor specified channels, fetching and processing new messages asynchronously."""
    client = TelegramClient(SESSION_PATH, TG_APP_ID, TG_APP_HASH)
    api_semaphore = asyncio.Semaphore(5)
    try:
        await client.start(phone=(lambda: TG_PHONE), password=(lambda: TG_PASSWORD), code_callback=code_callback)
        target_groups = await fetch_target_groups(client=client, semaphore=api_semaphore)
        channel_entities = [await client.get_entity(group.id) for group in target_groups]
        while True:
            for channel_entity in channel_entities:
                messages = await fetch_messages(channel_entity, client=client, semaphore=api_semaphore)
                await process_messages(messages, on_change=on_change)
            await asyncio.sleep(1 + random.random() * 5)
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        logger.error(traceback.format_exc())

    finally:
        await client.disconnect()


app = FastAPI()
main_app_lifespan = app.router.lifespan_context


@asynccontextmanager
async def lifespan_wrapper(app):
    monitor_task = asyncio.create_task(monitor_channels())
    try:
        async with main_app_lifespan(app) as maybe_state:
            yield maybe_state
    except Exception as e:
        logger.error(f"Lifespan Exception: {e}")
        raise
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


app.router.lifespan_context = lifespan_wrapper


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
