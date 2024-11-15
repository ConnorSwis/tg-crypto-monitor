import os
import json
import asyncio

class PersistentSet:
    def __init__(self, file_name):
        self.file_name = file_name
        self._set = set()
        self._lock = asyncio.Lock()  # Lock to ensure thread safety

        # Load set from file if it exists
        if os.path.exists(self.file_name):
            with open(self.file_name, 'r') as file:
                try:
                    data = json.load(file)
                    self._set = set(data)
                except json.JSONDecodeError:
                    self._set = set()

    async def _save_to_file(self):
        """Save the set as a list to the file system."""
        async with self._lock:  # Ensure file write operations are synchronized
            with open(self.file_name, 'w') as file:
                json.dump(list(self._set), file)

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
