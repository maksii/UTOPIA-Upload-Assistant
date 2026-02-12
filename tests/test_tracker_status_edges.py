import unittest
from unittest import mock

from src import trackerstatus
from tests.conftest import FakeTracker, FakeTrackerSetup


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
            mock.patch.object(trackerstatus.cli_ui, "ask_string", return_value="y"),
        ):
            manager = trackerstatus.TrackerStatusManager(config)
            await manager.process_all_trackers(meta)

        status = meta["tracker_status"]["FAKE"]
        self.assertTrue(status["upload"], msg="FAKE tracker should be marked for upload after rename confirm")
        self.assertFalse(status["dupe"], msg="No dupe was returned so dupe should be False")
        self.assertTrue(
            any("applies a naming change" in str(call.args[0]) for call in console_print.call_args_list),
            msg="Console should print naming change message",
        )

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
        self.assertTrue(status["dupe"], msg="When dupe_check returns True, status should be dupe")
        self.assertFalse(status["upload"], msg="Dupe should block upload")

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

        ask_string = mock.Mock(side_effect=["tt1234567", "y"])
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
        self.assertTrue(status["upload"], msg="THR upload should be True after providing IMDB and confirming")
        self.assertGreaterEqual(ask_string.call_count, 1, msg="ask_string should be called at least for IMDB prompt")
        prompt_messages = [call.args[0] if call.args else "" for call in ask_string.call_args_list]
        self.assertTrue(any("IMDB" in msg or "imdb" in msg.lower() for msg in prompt_messages), msg="Expected ask_string to be called for IMDB id prompt")


if __name__ == "__main__":
    unittest.main()
