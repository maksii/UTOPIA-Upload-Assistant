import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bs4.element import AttributeValueList

from src.get_disc import DiscInfoManager
from src.get_source import get_source
from src.get_tracker_data import TrackerDataManager
from src.getseasonep import _safe_int
from src.imdb import ImdbManager
from src.is_scene import SceneManager
from src.languages import LanguagesManager
from src.manualpackage import ManualPackageManager
from src.metadata_searching import _coerce_int
from src.nfo_link import NfoLinkManager


class GetDiscTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_dvd_size_groups_duplicates(self) -> None:
        manager = DiscInfoManager({"DEFAULT": {}})
        discs = [
            {"size": "4.7"},
            {"size": "4.7"},
            {"size": "8.5"},
        ]

        result = await manager.get_dvd_size(discs, manual_dvds=None)

        self.assertEqual(result, "2x4.7 8.5")


class GetSourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_manual_source_overrides_guess(self) -> None:
        source, out_type = await get_source("ENCODE", "Video.mkv", "Video.mkv", "", {"manual_source": "Web", "debug": False}, "abc", "/tmp")

        self.assertEqual(source, "Web")
        self.assertEqual(out_type, "WEBRIP")

    async def test_dvd_system_from_mediainfo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            tmp_dir = base_dir / "tmp" / "abc"
            tmp_dir.mkdir(parents=True)
            media = {"media": {"track": [{"@type": "General"}, {"@type": "Video", "Standard": "PAL"}]}}
            (tmp_dir / "MediaInfo.json").write_text(json.dumps(media), encoding="utf-8")

            meta = {"debug": False, "is_disc": "DVD"}
            source, out_type = await get_source("REMUX", "Video.mkv", "Video.mkv", "DVD", meta, "abc", str(base_dir))

            self.assertEqual(source, "PAL DVD")
            self.assertEqual(out_type, "REMUX")


class TrackerDataTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_available_trackers_respects_cooldown(self) -> None:
        manager = TrackerDataManager({"DEFAULT": {}, "TRACKERS": {}})
        with mock.patch.object(manager, "get_tracker_timestamps", return_value={"PTP": 95.0, "AITHER": 90.0}), mock.patch("src.get_tracker_data.time.time", return_value=100.0):
            available, waiting = await manager.get_available_trackers(["PTP", "AITHER"], base_dir="/tmp")

        self.assertEqual(available, [])
        self.assertEqual({name for name, _ in waiting}, {"PTP", "AITHER"})


class SeasonEpisodeTests(unittest.TestCase):
    def test_safe_int_default(self) -> None:
        self.assertEqual(_safe_int("bad", 7), 7)
        self.assertEqual(_safe_int("5", 0), 5)


class ImdbTests(unittest.TestCase):
    def test_safe_get_returns_default(self) -> None:
        manager = ImdbManager()
        result = manager.safe_get({"a": {"b": 3}}, ["a", "missing"], 0)

        self.assertEqual(result, 0)


class SceneTests(unittest.TestCase):
    def test_attr_to_string(self) -> None:
        manager = SceneManager({"DEFAULT": {}})

        self.assertEqual(manager._attr_to_string("value"), "value")
        self.assertEqual(manager._attr_to_string(AttributeValueList(["a", "b"])), "a b")
        self.assertEqual(manager._attr_to_string(None), "")


class LanguagesTests(unittest.IsolatedAsyncioTestCase):
    async def test_parse_blu_ray_extracts_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            tmp_dir = base_dir / "tmp" / "abc"
            tmp_dir.mkdir(parents=True)
            content = """Disc Title: Sample\nAudio: English / DTS-HD MA / 5.1 / 48 kHz / 3000 kbps / 24-bit\nSubtitle: English / 50 kbps\n"""
            (tmp_dir / "BD_SUMMARY_00.txt").write_text(content, encoding="utf-8")

            manager = LanguagesManager()
            parsed = await manager.parse_blu_ray({"base_dir": str(base_dir), "uuid": "abc"})

            self.assertEqual(parsed["audio"][0]["language"], "English")
            self.assertEqual(parsed["subtitles"][0]["language"], "English")


class ManualPackageTests(unittest.IsolatedAsyncioTestCase):
    async def test_package_uses_filebrowser_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            tmp_dir = base_dir / "tmp" / "abc"
            tmp_dir.mkdir(parents=True)
            (tmp_dir / "BASE.torrent").write_text("fake", encoding="utf-8")

            config = {
                "DEFAULT": {},
                "TRACKERS": {"MANUAL": {"filebrowser": "https://files.example"}},
            }
            manager = ManualPackageManager(config)
            meta = {
                "base_dir": str(base_dir),
                "uuid": "abc",
                "name": "Sample Name",
                "overview": "Overview",
                "resolution": "1080p",
                "source": "BluRay",
                "type": "REMUX",
                "tag": "",
                "category": "MOVIE",
                "tmdb": "123",
                "imdb_id": 0,
                "tvdb_id": 0,
                "image_list": [],
                "title": "Sample Title",
                "path": str(base_dir / "Sample.mkv"),
                "poster": None,
                "rehosted_poster": None,
                "skip_imghost_upload": True,
                "debug": False,
                "is_disc": "",
            }

            with (
                mock.patch("src.manualpackage.shutil.make_archive"),
                mock.patch("src.manualpackage.Torrent.read", return_value=mock.Mock()),
                mock.patch(
                    "src.manualpackage.Torrent.copy",
                    return_value=mock.Mock(write=mock.Mock()),
                ),
            ):
                url = await manager.package(meta)

        self.assertEqual(url, "https://files.example/tmp/abc")


class MetadataSearchingTests(unittest.TestCase):
    def test_coerce_int(self) -> None:
        self.assertIsNone(_coerce_int("bad"))
        self.assertEqual(_coerce_int("9"), 9)


class NfoLinkTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_season_nfo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = NfoLinkManager({"DEFAULT": {}})
            season_path = await manager.create_season_nfo(
                temp_dir,
                season_number="1",
                season_year="2024",
                tvdbid="123",
                tvmazeid="456",
                plot="Plot",
                outline="Outline",
            )

            content = Path(season_path).read_text(encoding="utf-8")

        self.assertIn("<seasonnumber>1</seasonnumber>", content)


if __name__ == "__main__":
    unittest.main()
