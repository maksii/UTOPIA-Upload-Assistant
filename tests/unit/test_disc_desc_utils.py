import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bs4.element import AttributeValueList
from rich.console import Console

from src.console import console
from src.cookie_auth import _attr_to_string
from src.disc_menus import DiscMenus
from src.discparse import DiscParse
from src.dupe_checking import DupeChecker
from src.edition import format_duration, smart_title
from src.exceptions import LoginException, UploadException
from src.exportmi import mi_resolution, validate_file_path
from src.get_desc import html_to_bbcode


class ConsoleTests(unittest.TestCase):
    def test_console_instance(self) -> None:
        self.assertIsInstance(console, Console)


class CookieAuthTests(unittest.TestCase):
    def test_attr_to_string_handles_types(self) -> None:
        self.assertEqual(_attr_to_string("value"), "value")
        self.assertEqual(_attr_to_string(AttributeValueList(["a", "b"])), "a b")
        self.assertEqual(_attr_to_string(None), "")


class DiscMenusTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_local_images_uploads_and_saves_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            menu_dir = Path(temp_dir) / "menus"
            menu_dir.mkdir()
            (menu_dir / "menu1.jpg").write_text("x", encoding="utf-8")
            (menu_dir / "menu2.png").write_text("y", encoding="utf-8")

            meta = {
                "path_to_menu_screenshots": str(menu_dir),
                "base_dir": temp_dir,
                "uuid": "abc",
            }

            config: dict[str, dict[str, str]] = {"DEFAULT": {}}
            manager = DiscMenus(meta, config)

            uploaded = [{"img_url": "https://img.example/1"}, {"img_url": "https://img.example/2"}]
            with mock.patch.object(
                manager.uploadscreens_manager,
                "upload_screens",
                new=mock.AsyncMock(return_value=(uploaded, {})),
            ):
                await manager.get_local_images(meta)

            self.assertEqual(meta["menu_images"], uploaded)
            saved = Path(temp_dir) / "tmp" / "abc" / "menu_images.json"
            self.assertTrue(saved.exists())
            data = json.loads(saved.read_text(encoding="utf-8"))
            self.assertEqual(len(data["menu_images"]), 2)


class DiscParseTests(unittest.TestCase):
    def test_setup_mediainfo_for_dvd_uses_cached_config(self) -> None:
        parser = DiscParse({"DEFAULT": {}})
        parser.mediainfo_config = {"cli": "/tmp/mediainfo"}
        cli = parser.setup_mediainfo_for_dvd("/tmp")
        self.assertEqual(cli, "/tmp/mediainfo")

    def test_setup_mediainfo_for_dvd_calls_setup(self) -> None:
        parser = DiscParse({"DEFAULT": {}})
        with mock.patch("src.discparse.setup_mediainfo_library", return_value={"cli": "/tmp/mediainfo"}):
            cli = parser.setup_mediainfo_for_dvd("/tmp")
        self.assertEqual(cli, "/tmp/mediainfo")


class DupeCheckerTests(unittest.IsolatedAsyncioTestCase):
    async def test_normalize_filename_accepts_dict(self) -> None:
        normalized = await DupeChecker.normalize_filename({"name": "Sample.Movie.2024"})
        self.assertEqual(normalized, "sample movie 2024")

    async def test_refine_hdr_terms(self) -> None:
        terms = await DupeChecker.refine_hdr_terms("DV HDR10+")
        self.assertEqual(terms, {"DV", "HDR"})


class EditionTests(unittest.TestCase):
    def test_format_duration(self) -> None:
        self.assertEqual(format_duration(3661), "1:01:01")

    def test_smart_title(self) -> None:
        self.assertEqual(smart_title("director's cut"), "Director's Cut")


class ExceptionsTests(unittest.TestCase):
    def test_login_exception_default_message(self) -> None:
        self.assertEqual(str(LoginException()), "An error occurred while logging in")

    def test_upload_exception_default_message(self) -> None:
        self.assertEqual(str(UploadException()), "An error occurred while uploading")


class ExportMiTests(unittest.IsolatedAsyncioTestCase):
    async def test_mi_resolution_maps_known(self) -> None:
        result = await mi_resolution("1920x1080p", {"screen_size": "1920x1080p"}, 1920, "p")
        self.assertEqual(result, "1080p")

    async def test_mi_resolution_uses_width_fallback(self) -> None:
        result = await mi_resolution("unknown", {}, 1280, "p")
        self.assertEqual(result, "720p")

    def test_validate_file_path_errors(self) -> None:
        with self.assertRaises(ValueError):
            validate_file_path("")
        with self.assertRaises(ValueError):
            validate_file_path("/path/does/not/exist.mkv")


class GetDescTests(unittest.TestCase):
    def test_html_to_bbcode(self) -> None:
        html = "<b>Title</b><br>Line"
        self.assertEqual(html_to_bbcode(html), "[b]Title[/b]\nLine")


if __name__ == "__main__":
    unittest.main()
