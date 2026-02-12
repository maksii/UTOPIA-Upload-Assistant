from __future__ import annotations

import os


def safe_join(directory: str, *pathnames: str) -> str | None:
    if not directory:
        return None
    return os.path.join(directory, *pathnames)
