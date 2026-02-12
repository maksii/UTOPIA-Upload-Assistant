import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.add_comparison import ComparisonManager
from src.apply_overrides import ApplyOverrides
from src.audio import is_atmos_or_immersive_audio
from src.bbcode import BBCODE
from src.bdinfo_comparator import generate_warning, normalize_and_filter, remove_formatting, sorting_priority
from src.bluray_com import _style_gray, _style_green, _style_specs
from src.btnid import BtnIdManager
from src.cleanup import CleanupManager, running_subprocesses
from src.clients import Clients
from tests.conftest import FakeResponse


class ComparisonManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_load_saved_comparison_updates_image_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            comparison_dir = base_dir / "comparisons"
            comparison_dir.mkdir(parents=True)
            tmp_dir = base_dir / "tmp" / "abc"
            tmp_dir.mkdir(parents=True)
            comparison_data = {"1": {"urls": [{"img_url": "https://img.example/1.png", "raw_url": "https://img.example/1.png", "web_url": "https://img.example/1"}]}}
            (tmp_dir / "comparison_data.json").write_text(json.dumps(comparison_data), encoding="utf-8")

            meta = {
                "comparison": str(comparison_dir),
                "base_dir": str(base_dir),
                "uuid": "abc",
                "comparison_index": "1",
                "debug": False,
            }
            manager = ComparisonManager(meta, {"DEFAULT": {}})

            loaded = await manager.add_comparison()

            self.assertIn("1", loaded)
            self.assertEqual(len(meta.get("image_list", [])), 1)


class ApplyOverridesTests(unittest.IsolatedAsyncioTestCase):
    async def test_apply_args_updates_ids(self) -> None:
        config = {"DEFAULT": {"screens": 3}}
        meta = {"path": "/data/video.mkv", "category": "MOVIE", "debug": False}
        overrides = ApplyOverrides(config)

        updated = await overrides.apply_args_to_meta(meta, ["--imdb", "tt1234567", "--tmdb", "555"])

        self.assertEqual(updated["imdb_id"], 1234567)
        self.assertEqual(updated["tmdb_id"], 555)


class AudioHelperTests(unittest.TestCase):
    def test_is_atmos_or_immersive_audio(self) -> None:
        self.assertTrue(is_atmos_or_immersive_audio("Dolby Atmos", "TrueHD", "7.1"))
        self.assertFalse(is_atmos_or_immersive_audio("", "AAC", "2.0"))


class BbcodeTests(unittest.TestCase):
    def test_clean_hdb_description_removes_hdbits(self) -> None:
        bbcode = BBCODE()
        description = "[url=https://t.hdbits.org/details.php?id=123][/url]\n[url=https://imgbox.com/abc][img]https://thumbs2.imgbox.com/xx_t.png[/img][/url]"

        cleaned, images = bbcode.clean_hdb_description(description)

        self.assertNotIn("hdbits.org", cleaned)
        self.assertEqual(len(images), 1)


class BdinfoComparatorTests(unittest.TestCase):
    def test_remove_formatting_strips_tags(self) -> None:
        text = "[b]Video[/b]<br>Subtitle: 123 kbps"

        cleaned = remove_formatting(text)

        self.assertNotIn("[b]", cleaned)
        self.assertIn("Subtitle", cleaned)

    def test_normalize_and_filter_keeps_bitrate_lines(self) -> None:
        content = "Video: AVC / 12000 kbps\nOther line"

        lines = normalize_and_filter(content)

        self.assertEqual(lines, ["Video: AVC / 12000 kbps"])

    def test_generate_warning_for_missing_content(self) -> None:
        warning = generate_warning("Sample", "", True)

        self.assertIn("No BDInfo", warning)

    def test_sorting_priority_prefers_video(self) -> None:
        priority = sorting_priority({"content": "Video: AVC 23.976 fps"})

        self.assertEqual(priority[0], 0)


class BlurayStyleTests(unittest.TestCase):
    def test_style_helpers(self) -> None:
        self.assertTrue(_style_green("color: green;"))
        self.assertTrue(_style_gray("color: #999999;"))
        self.assertTrue(_style_specs("font-size: 12px;"))


class BtnIdTests(unittest.IsolatedAsyncioTestCase):
    async def test_btn_error_returns_zeroes(self) -> None:
        error_response = FakeResponse({"error": {"code": 401, "message": "Unauthorized IP"}})

        async def fake_post(*_args, **_kwargs):
            return error_response

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

            post = staticmethod(fake_post)

        with mock.patch("src.btnid.httpx.AsyncClient", return_value=FakeClient()):
            imdb_id, tvdb_id = await BtnIdManager.get_btn_torrents("api", "123", {"debug": False})

        self.assertEqual(imdb_id, 0)
        self.assertEqual(tvdb_id, 0)


class CleanupTests(unittest.TestCase):
    def test_kill_all_threads_android_path(self) -> None:
        manager = CleanupManager()
        fake_proc = mock.Mock()
        fake_proc.returncode = None
        running_subprocesses.add(fake_proc)

        with mock.patch("src.cleanup.IS_ANDROID", True):
            manager.kill_all_threads()

        self.assertTrue(fake_proc.terminate.called)
        running_subprocesses.clear()


class ClientsTests(unittest.TestCase):
    def test_extract_tracker_ids_from_comment(self) -> None:
        comment = "PTP https://passthepopcorn.me/torrents.php?torrentid=123 Aither https://aither.cc/torrents/456"

        ids = Clients._extract_tracker_ids_from_comment(comment)

        self.assertEqual(ids["ptp"], "123")
        self.assertEqual(ids["aither"], "456")


if __name__ == "__main__":
    unittest.main()
