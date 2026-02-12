import asyncio
import os as _os
from pathlib import Path


async def listdir(path: str | Path):
    return await asyncio.to_thread(_os.listdir, path)
