import unittest
from typing import Any, Optional
from unittest import mock

from src import trackerstatus


class FakeTracker:
    tracker = "FAKE"
    banned_groups = []

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def search_existing(self, _meta: dict[str, Any], _disctype: Optional[str]):
        return []

    async def get_name(self, _meta: dict[str, Any]):
        return {"name": "Renamed Release"}


class FakeTrackerSetup:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def check_banned_group(self, *_args, **_kwargs):
        return False

    async def get_torrent_claims(self, *_args, **_kwargs):
        return False


class TrackerStatusEdgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_tracker_rename_and_passed_checks(self) -> None:
        meta = {
            "trackers": ["FAKE"],
            "tracker_status": {},
            "name": "Original Release",
            "debug": False,
            "unattended": True,
            "unattended_confirm": True,
            "imdb_id": 1234567,
            "imdb": "1234567",
            "category": "MOVIE",
        }
        config = {"DEFAULT": {}, "TRACKERS": {"FAKE": {"api_key": "fake"}}}

        with (
            mock.patch.object(trackerstatus, "tracker_class_map", {"FAKE": FakeTracker}),
            mock.patch.object(trackerstatus, "TRACKER_SETUP", FakeTrackerSetup),
            mock.patch.object(trackerstatus.DupeChecker, "filter_dupes", return_value=[]),
            mock.patch.object(trackerstatus.UploadHelper, "dupe_check", return_value=(False, meta)),
            mock.patch.object(trackerstatus.console, "print") as console_print,
        ):
            manager = trackerstatus.TrackerStatusManager(config)
            await manager.process_all_trackers(meta)

        status = meta["tracker_status"]["FAKE"]
        self.assertTrue(status["upload"])
        self.assertFalse(status["dupe"])
        self.assertTrue(any("applies a naming change" in str(call.args[0]) for call in console_print.call_args_list))

    async def test_duplicate_rule_blocks_upload(self) -> None:
        meta = {
            "trackers": ["FAKE"],
            "tracker_status": {},
            "name": "Original Release",
            "debug": False,
            "unattended": True,
            "unattended_confirm": True,
            "imdb_id": 1234567,
            "imdb": "1234567",
            "category": "MOVIE",
        }
        config = {"DEFAULT": {}, "TRACKERS": {"FAKE": {"api_key": "fake"}}}

        with (
            mock.patch.object(trackerstatus, "tracker_class_map", {"FAKE": FakeTracker}),
            mock.patch.object(trackerstatus, "TRACKER_SETUP", FakeTrackerSetup),
            mock.patch.object(trackerstatus.DupeChecker, "filter_dupes", return_value=[{"name": "Dupe"}]),
            mock.patch.object(trackerstatus.UploadHelper, "dupe_check", return_value=(True, meta)),
        ):
            manager = trackerstatus.TrackerStatusManager(config)
            await manager.process_all_trackers(meta)

        status = meta["tracker_status"]["FAKE"]
        self.assertTrue(status["dupe"])
        self.assertFalse(status["upload"])

    async def test_missing_imdb_prompts_for_id(self) -> None:
        meta = {
            "trackers": ["THR"],
            "tracker_status": {},
            "name": "Original Release",
            "debug": False,
            "unattended": False,
            "unattended_confirm": False,
            "imdb_id": 0,
            "imdb": "",
            "category": "MOVIE",
        }
        config = {"DEFAULT": {}, "TRACKERS": {"THR": {"api_key": "fake"}}}

        class FakeTHR(FakeTracker):
            tracker = "THR"

        ask_string = mock.Mock(return_value="tt1234567")
        with (
            mock.patch.object(trackerstatus, "tracker_class_map", {"THR": FakeTHR}),
            mock.patch.object(trackerstatus, "TRACKER_SETUP", FakeTrackerSetup),
            mock.patch.object(trackerstatus.DupeChecker, "filter_dupes", return_value=[]),
            mock.patch.object(trackerstatus.UploadHelper, "dupe_check", return_value=(False, meta)),
            mock.patch.object(trackerstatus.cli_ui, "ask_string", ask_string),
            mock.patch.object(trackerstatus.imdb_manager, "get_imdb_info_api", return_value={}),
            mock.patch("builtins.input", return_value="y"),
        ):
            manager = trackerstatus.TrackerStatusManager(config)
            await manager.process_all_trackers(meta)

        status = meta["tracker_status"]["THR"]
        self.assertTrue(status["upload"])
        ask_string.assert_called_once()


if __name__ == "__main__":
    unittest.main()
