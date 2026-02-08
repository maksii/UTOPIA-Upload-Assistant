import tempfile
import unittest
from pathlib import Path

from src import trackermeta
from src.prep import _normalize_search_year, _to_int
from src.qbitwait import Wait
from src.queuemanage import QueueManager
from src.radarr import RadarrManager
from src.rehostimages import _as_str, _safe_remove, sanitize_filename
from src.search import Search
from src.sonarr import SonarrManager
from src.trackerhandle import check_mod_q_and_draft
from src.trackermeta import TrackerMetaManager
from src.tvdb import _as_dict_list, _coerce_int


class PrepHelpersTests(unittest.TestCase):
    def test_normalize_search_year(self) -> None:
        self.assertIsNone(_normalize_search_year(None))
        self.assertEqual(_normalize_search_year(2024), "2024")

    def test_to_int_default(self) -> None:
        self.assertEqual(_to_int("bad", 3), 3)
        self.assertEqual(_to_int("7", 0), 7)


class QbitWaitTests(unittest.TestCase):
    def test_missing_default_client_config(self) -> None:
        with self.assertRaises(ValueError):
            Wait({"DEFAULT": {}, "TORRENT_CLIENTS": {}})


class QueueManageTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_log_file_and_load_processed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = await QueueManager.get_log_file(temp_dir, "My Queue")
            self.assertTrue(log_file.endswith("My_Queue_processed_files.log"))

            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            Path(log_file).write_text('["/path/one"]', encoding="utf-8")
            loaded = await QueueManager.load_processed_files(log_file)

        self.assertEqual(loaded, {"/path/one"})


class RadarrTests(unittest.IsolatedAsyncioTestCase):
    async def test_extract_movie_data_empty_list(self) -> None:
        manager = RadarrManager({"DEFAULT": {}, "RADARR": {}})
        data = await manager.extract_movie_data([])

        self.assertIsNone(data["imdb_id"])
        self.assertEqual(data["genres"], [])


class RehostImagesTests(unittest.IsolatedAsyncioTestCase):
    async def test_helpers(self) -> None:
        self.assertEqual(_as_str(None), None)
        self.assertEqual(_as_str(5), None)

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "sample.txt"
            file_path.write_text("x", encoding="utf-8")
            self.assertTrue(_safe_remove(str(file_path)))

        sanitized = await sanitize_filename("Sample File.png")
        self.assertIn("Sample", sanitized)


class SearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_search_dirs(self) -> None:
        search = Search({"DISCORD": {"search_dir": ["/tmp", "/data"]}})
        self.assertEqual(search._get_search_dirs(), ["/tmp", "/data"])

    async def test_file_search(self) -> None:
        search = Search({"DISCORD": {"search_dir": []}})
        self.assertTrue(await search.file_search("sample file", ["sample"]))
        self.assertFalse(await search.file_search("sample", ["missing"]))


class SonarrTests(unittest.IsolatedAsyncioTestCase):
    async def test_extract_show_data_parse_response(self) -> None:
        manager = SonarrManager({"DEFAULT": {}, "SONARR": {}})
        payload = {
            "series": {"tvdbId": 10, "imdbId": "tt123", "tvMazeId": 55, "tmdbId": 99, "genres": ["Drama"], "year": 2020},
            "parsedEpisodeInfo": {"releaseGroup": "GROUP"},
        }
        data = await manager.extract_show_data(payload)

        self.assertEqual(data["imdb_id"], 123)
        self.assertEqual(data["release_group"], "GROUP")


class TrackerHandleTests(unittest.IsolatedAsyncioTestCase):
    async def test_check_mod_q_and_draft(self) -> None:
        class FakeTracker:
            tracker = "AITHER"

            async def get_flag(self, _meta, _flag):
                return "true"

        modq, draft, caps = await check_mod_q_and_draft(FakeTracker(), {"debug": False})

        self.assertEqual(modq, "Yes")
        self.assertIsNone(draft)
        self.assertTrue(caps["mod_q"])


class TrackerMetaTests(unittest.IsolatedAsyncioTestCase):
    async def test_apply_config_sets_expected_images(self) -> None:
        TrackerMetaManager({"DEFAULT": {"screens": 2}, "TRACKERS": {}})

        self.assertEqual(trackermeta.expected_images, 2)


class TvdbTests(unittest.TestCase):
    def test_tvdb_helpers(self) -> None:
        self.assertEqual(_coerce_int("5"), 5)
        self.assertIsNone(_coerce_int("bad"))

        parsed = _as_dict_list([{"a": 1}, "bad"])
        self.assertEqual(parsed, [{"a": 1}])


if __name__ == "__main__":
    unittest.main()
