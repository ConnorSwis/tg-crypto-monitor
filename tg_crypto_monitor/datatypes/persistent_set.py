import json
import asyncio
import aiofiles
from pathlib import Path


class PersistentSet:
    def __init__(self, path: Path):
        self.path = path
        self._set = set()
        self._lock = asyncio.Lock()  # Lock to ensure thread safety

    async def load(self):
        """Load the set from the file system."""
        if not self.path.exists():
            async with aiofiles.open(self.path, mode='w') as file:
                await file.write("[]")
        async with aiofiles.open(self.path, mode='r') as file:
            data = await file.read()
            try:
                self._set = set(json.loads(data))
            except json.JSONDecodeError:
                self._set = set()

    async def _save_to_file(self):
        """Save the set as a list to the file system."""
        async with self._lock:
            async with aiofiles.open(self.path, mode='w') as file:
                await file.write(json.dumps(list(self._set)))

    async def add(self, item):
        """Add an item to the set and save to file."""
        async with self._lock:
            self._set.add(item)
        await self._save_to_file()

    async def remove(self, item):
        """Remove an item from the set and save to file."""
        async with self._lock:
            self._set.remove(item)
        await self._save_to_file()

    async def discard(self, item):
        """Remove an item from the set if it exists, and save to file."""
        async with self._lock:
            self._set.discard(item)
        await self._save_to_file()

    async def clear(self):
        """Clear all items from the set and save to file."""
        async with self._lock:
            self._set.clear()
        await self._save_to_file()

    async def update(self, *args):
        """Update the set with multiple items and save to file."""
        async with self._lock:
            self._set.update(*args)
        await self._save_to_file()

    async def contains(self, item):
        """Check if an item is in the set."""
        async with self._lock:
            return item in self._set

    async def size(self):
        """Return the size of the set."""
        async with self._lock:
            return len(self._set)

    async def to_list(self):
        """Return a list representation of the set."""
        async with self._lock:
            return list(self._set)

    def __repr__(self):
        """Return a string representation of the set."""
        return f"{self.__class__.__name__}({list(self._set)})"
