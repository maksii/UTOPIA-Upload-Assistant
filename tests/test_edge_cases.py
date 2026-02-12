import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import exportmi, takescreens, tmdb
from src.audio import bloated_check
from src.clients import Clients
from src.edition import get_edition
from src.get_name import NameManager
from src.uphelper import UploadHelper
from tests.conftest import FakeDupeTracker, FakeFFmpegCommand


class EdgeCaseTests(unittest.IsolatedAsyncioTestCase):
    def test_validate_file_path_missing(self) -> None:
        with self.assertRaises(ValueError):
            exportmi.validate_file_path("/tmp/does-not-exist.mkv")

    async def test_get_frame_info_handles_ffmpeg_exception(self) -> None:
        async def fake_run_ffmpeg(_command):
            raise RuntimeError("ffmpeg failed")

        fake_ffmpeg = mock.Mock()
        fake_ffmpeg.input.return_value = FakeFFmpegCommand()

        with mock.patch("src.takescreens.run_ffmpeg", side_effect=fake_run_ffmpeg), mock.patch("src.takescreens.ffmpeg", fake_ffmpeg):
            meta = {"frame_rate": 24.0, "debug": False}
            info = await takescreens.get_frame_info("video.mkv", 1.0, meta)

        self.assertEqual(info["frame_type"], "Unknown")
        self.assertEqual(info["frame_number"], 24)

    async def test_manual_edition_and_tag_override_name(self) -> None:
        edition, repack, webdv = await get_edition(
            "Sample.Movie.2025.REPACK.mkv",
            None,
            ["Sample.Movie.2025.REPACK.mkv"],
            ["Director's Cut", "REPACK"],
            {"category": "MOVIE", "anime": False, "debug": False, "tag": "-FAKE", "webdv": False},
        )
        meta = {
            "category": "MOVIE",
            "type": "WEBDL",
            "title": "Sample Movie",
            "aka": "",
            "year": "2025",
            "manual_year": None,
            "resolution": "2160p",
            "audio": "TrueHD 7.1",
            "service": "MA",
            "season": "",
            "episode": "",
            "part": "",
            "repack": repack,
            "3D": "",
            "tag": "-FAKE",
            "source": "WEB-DL",
            "uhd": "",
            "hdr": "DV",
            "webdv": webdv,
            "manual_episode_title": "",
            "daily_episode_title": "",
            "video_codec": "",
            "video_encode": "H.265",
            "is_disc": False,
            "edition": edition,
            "category_override": None,
            "no_season": False,
            "no_year": False,
            "no_aka": False,
            "debug": False,
            "trackers": [],
            "type_override": None,
            "search_year": "2025",
        }
        manager = NameManager({"DEFAULT": {}, "TRACKERS": {}})
        name_notag, name, _clean_name, _missing = await manager.get_name(meta)

        self.assertIn("DIRECTOR'S CUT", name, msg="Edition should appear in release name")
        self.assertIn("REPACK", name, msg="Repack tag should appear in release name")
        self.assertIn("WEB-DL", name, msg="Source WEB-DL should appear in release name")
        self.assertTrue(name.endswith("-FAKE"), msg="Release name should end with manual tag -FAKE")
        self.assertIn("Sample Movie", name_notag, msg="Name without tag should contain title")

    async def test_missing_tmdb_id_requires_manual_entry(self) -> None:
        with (
            mock.patch.object(tmdb, "get_tmdb_id", return_value=(0, "MOVIE")),
            mock.patch.object(tmdb, "guessit_fn", return_value={"title": "Sample Movie"}),
            mock.patch("builtins.exit", side_effect=SystemExit) as exit_mock,
        ):
            with self.assertRaises(SystemExit):
                await tmdb.tmdb_other_meta(
                    tmdb_id=0,
                    path="Sample.Movie.2024.1080p.WEB-DL.mkv",
                    search_year=2024,
                    category="MOVIE",
                    imdb_id=0,
                    debug=False,
                    mode="cli",
                )
            exit_mock.assert_called_once()

    def test_bloated_audio_sets_flag(self) -> None:
        meta = {"trackers": ["BHD"], "bloated": False, "debug": False}
        bloated_check(meta, ["fr"], is_eng_original_with_non_eng=True)

        self.assertTrue(meta["bloated"], msg="Bloated audio check should set bloated flag")
        self.assertNotIn("BHD", meta["trackers"], msg="BHD should be removed from trackers when bloated")

    async def test_trumpable_dupe_sets_trumping(self) -> None:
        config = {"DEFAULT": {}, "TRACKERS": {"FAKE": {"api_key": "fake"}}}
        meta = {
            "unattended": False,
            "unattended_confirm": False,
            "ask_dupe": False,
            "dupe": False,
            "trumpable_id": 123,
            "matched_episode_ids": [],
            "filename_match": False,
            "file_count_match": False,
            "tag": "",
            "tv_pack": False,
            "debug": False,
            "name": "Sample Release",
            "category": "MOVIE",
        }
        dupes = [{"name": "Sample.Dupe", "link": "https://tracker.example/1", "trumpable": True}]

        with mock.patch("src.uphelper.tracker_class_map", {"FAKE": FakeDupeTracker}), mock.patch("src.uphelper.cli_ui.ask_yes_no", return_value=True):
            helper = UploadHelper(config)
            helper.tracker_class_map = {"FAKE": FakeDupeTracker}
            is_dupe, updated = await helper.dupe_check(dupes, meta, "FAKE")

        self.assertFalse(is_dupe, msg="User chose to trump so release should not be treated as dupe")
        self.assertTrue(updated["were_trumping"], msg="Meta should record that we are trumping")
        self.assertEqual(updated["trump_reason"], "trumpable_release", msg="Trump reason should be set")


class TorrentClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_adds_torrent_to_client(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            uuid = "test"
            torrent_dir = base_dir / "tmp" / uuid
            torrent_dir.mkdir(parents=True, exist_ok=True)
            content_path = base_dir / "sample.mkv"
            content_path.write_bytes(b"fake")
            torrent_path = torrent_dir / "[FAKE].torrent"

            from torf import Torrent

            torrent = Torrent(path=str(content_path), trackers=["https://tracker.example/announce"], source="UA", private=True)
            torrent.generate()
            torrent.write(str(torrent_path), overwrite=True)

            config = {
                "DEFAULT": {
                    "default_torrent_client": "client1",
                },
                "TORRENT_CLIENTS": {
                    "client1": {
                        "torrent_client": "qbit",
                        "host": "http://localhost",
                        "username": "user",
                        "password": "pass",
                        "save_path": str(base_dir),
                    }
                },
            }
            meta = {
                "base_dir": str(base_dir),
                "uuid": uuid,
                "path": str(content_path),
                "debug": False,
                "is_disc": False,
                "filelist": [str(content_path)],
                "client": None,
            }
            clients = Clients(config=config)

            with mock.patch.object(clients, "qbittorrent") as qbittorrent:
                await clients.add_to_client(meta, "FAKE")

            qbittorrent.assert_called_once()


if __name__ == "__main__":
    unittest.main()
