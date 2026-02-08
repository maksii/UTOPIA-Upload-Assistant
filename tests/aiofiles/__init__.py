import asyncio
from pathlib import Path
from typing import Any

from . import os as os


class _AsyncFile:
    def __init__(self, file_obj) -> None:
        self._file = file_obj

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._file.close()

    async def read(self) -> str:
        return await asyncio.to_thread(self._file.read)

    async def write(self, data: str) -> int:
        return await asyncio.to_thread(self._file.write, data)

    async def read_text(self) -> str:
        return await asyncio.to_thread(self._file.read)

    async def write_text(self, data: str) -> int:
        return await asyncio.to_thread(self._file.write, data)


def open(
    file: str | Path,
    mode: str = "r",
    *,
    encoding: str | None = None,
    **kwargs: Any,
) -> _AsyncFile:
    file_obj = Path(file).open(mode=mode, encoding=encoding, **kwargs)  # noqa: SIM115
    return _AsyncFile(file_obj)
