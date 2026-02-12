"""
Shared test fixtures for the test suite.

Optional dependency stubs live in tests/_stubs/. To use them in minimal
environments (no real flask/aiohttp/etc.), prepend that directory to
sys.path before running tests.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

# ----- Shared Fake classes -----


class FakeFFmpegCommand:
    """Stub for ffmpeg-python command builder used in takescreens tests."""

    def __init__(self) -> None:
        self._cmd = ["ffmpeg", "-i", "input", "-filter", "showinfo"]

    def __getitem__(self, _key: str) -> FakeFFmpegCommand:
        return self

    def filter(self, _name: str) -> FakeFFmpegCommand:
        return self

    def output(self, *_args: Any, **_kwargs: Any) -> FakeFFmpegCommand:
        return self

    def global_args(self, *_args: Any) -> FakeFFmpegCommand:
        return self

    def compile(self) -> list[str]:
        return self._cmd


class FakeResponse:
    """Unified HTTP response stub; supports both GET (payload) and POST (status + payload)."""

    def __init__(self, payload: Any = None, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise ValueError("HTTP error")


class FakeAsyncClient:
    """Unified async HTTP client stub. Use get_payload for GET, post_response for POST."""

    def __init__(
        self,
        get_payload: Any = None,
        post_response: FakeResponse | None = None,
    ) -> None:
        self._get_payload = get_payload
        self._post_response = post_response

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        pass

    async def get(self, _url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        return FakeResponse(self._get_payload)

    async def post(self, _url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        if self._post_response is not None:
            return self._post_response
        return FakeResponse(self._get_payload)


class FakeTracker:
    """Base tracker stub with attributes used across scenario, status, and unit tests."""

    tracker = "FAKE"
    banned_groups: list[str] = []
    approved_image_hosts = ["imgbb"]
    torrent_url = "https://tracker.example/torrents/"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def search_existing(self, _meta: dict[str, Any], _disctype: str | None) -> list[Any]:
        return []

    async def get_name(self, _meta: dict[str, Any]) -> dict[str, Any]:
        return {"name": "Renamed Release"}

    async def check_image_hosts(self, _meta: dict[str, Any]) -> None:
        pass

    async def get_flag(self, _meta: dict[str, Any], _flag: str) -> str:
        return "true"


class FakeTrackerSetup:
    """Stub for tracker setup used in tracker status edge tests."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def check_banned_group(self, *_args: Any, **_kwargs: Any) -> bool:
        return False

    async def get_torrent_claims(self, *_args: Any, **_kwargs: Any) -> bool:
        return False


class FakeTrackerStatusManager:
    """Stub for TrackerStatusManager used in scenario tests."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def process_all_trackers(self, meta: dict[str, Any]) -> int:
        meta["tracker_status"] = {tracker: {"upload": True, "status_message": "OK", "torrent_id": 123} for tracker in meta.get("trackers", [])}
        return len(meta.get("trackers", []))


class FakeDupeTracker(FakeTracker):
    """Tracker stub that returns a renamed name (for dupe/trump tests)."""

    async def get_name(self, _meta: dict[str, Any]) -> dict[str, Any]:
        return {"name": "Renamed Release"}


# ----- Factory helpers -----


def make_config(
    default_overrides: dict[str, Any] | None = None,
    trackers_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a minimal valid config dict. Override only what the test needs."""
    config: dict[str, Any] = {
        "DEFAULT": {
            "screens": "3",
            "tmdb_api": "",
            "img_host_1": "imgbb",
            "imgbb_api": "",
        },
        "TRACKERS": {
            "default_trackers": "PTP",
            "PTP": {"api_key": "fake_ptp_key"},
        },
    }
    if default_overrides:
        config["DEFAULT"].update(default_overrides)
    if trackers_overrides:
        config["TRACKERS"].update(trackers_overrides)
    return config


def make_meta(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid meta dict. Override only what the test needs."""
    meta: dict[str, Any] = {
        "path": "/data/sample.mkv",
        "category": "MOVIE",
        "debug": False,
        "trackers": [],
        "tracker_status": {},
        "name": "Sample Release",
        "unattended": False,
        "unattended_confirm": False,
        "imdb_id": 0,
        "imdb": "",
        "tmdb_id": 0,
        "tvdb_id": 0,
    }
    meta.update(overrides)
    return meta


@contextmanager
def tmp_config(base_dir: Path, config_content: dict[str, Any] | None = None):
    """Context manager that writes a temporary config and restores the original on exit."""
    from pprint import pformat

    config_path = base_dir / "data" / "config.py"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    original: str | None = None
    if config_path.exists():
        original = config_path.read_text(encoding="utf-8")
    content = config_content or {
        "DEFAULT": {"tmdb_api": "fake", "img_host_1": "imgbb", "imgbb_api": "fake", "screens": "3"},
        "TRACKERS": {"default_trackers": "PTP", "PTP": {"api_key": "fake"}},
    }
    config_path.write_text(f"config = {pformat(content)}\n", encoding="utf-8")
    try:
        yield config_path
    finally:
        if original is None and config_path.exists():
            config_path.unlink()
        elif original is not None:
            config_path.write_text(original, encoding="utf-8")
