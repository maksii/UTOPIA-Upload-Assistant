import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from src.tvmaze import TvmazeManager
from src.type_utils import to_int
from src.video import VideoManager


class TvmazeTests(unittest.IsolatedAsyncioTestCase):
    async def test_tvmaze_manual_override_returns_tuple(self) -> None:
        manager = TvmazeManager()
        result = await manager.search_tvmaze(
            filename="Sample Show",
            year="2024",
            imdbID="tt1234567",
            tvdbID="123",
            tvmaze_manual="555",
            return_full_tuple=True,
        )

        self.assertEqual(result, (555, 1234567, 123))

    async def test_tvmaze_selects_first_result(self) -> None:
        manager = TvmazeManager()
        response = [{"show": {"id": 101, "name": "Sample Show", "externals": {"imdb": "tt0000001"}}}]
        with mock.patch.object(manager, "_make_tvmaze_request", return_value=response):
            result = await manager.search_tvmaze(
                filename="Sample Show",
                year="2024",
                imdbID=None,
                tvdbID="0",
            )

        self.assertEqual(result, 101)


class TypeUtilsTests(unittest.TestCase):
    def test_to_int_variants(self) -> None:
        self.assertEqual(to_int(True), 1)
        self.assertEqual(to_int(3.7), 3)
        self.assertEqual(to_int("bad", fallback=9), 9)


class VideoTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_uhd_from_guess(self) -> None:
        manager = VideoManager()
        guess = {"Source": "Blu-ray", "Other": "Ultra HD"}
        result = await manager.get_uhd("DISC", guess, "1080p", "movie.mkv")

        self.assertEqual(result, "UHD")

    async def test_get_video_encode_for_webrip(self) -> None:
        manager = VideoManager()
        mi = {
            "media": {
                "track": [
                    {"@type": "General"},
                    {
                        "@type": "Video",
                        "Format": "AVC",
                        "Format_Profile": "High",
                        "BitDepth": "8",
                    },
                ]
            }
        }
        video_encode, codec, has_settings, bit_depth = await manager.get_video_encode(mi, "WEBRIP", None)

        self.assertEqual(video_encode.strip(), "x264")
        self.assertEqual(codec, "AVC")
        self.assertFalse(has_settings)
        self.assertEqual(bit_depth, "8")


class VsTests(unittest.TestCase):
    def test_optimize_images_noop_when_disabled(self) -> None:
        def _noop(*_args, **_kwargs):
            return None

        fake_vs = SimpleNamespace(core=SimpleNamespace())
        fake_awsm = SimpleNamespace(
            DynamicTonemap=_noop,
            ScreenGen=_noop,
            zresize=_noop,
        )

        with mock.patch.dict(sys.modules, {"vapoursynth": fake_vs, "awsmfunc": fake_awsm}):
            vs_module = importlib.import_module("src.vs")
            importlib.reload(vs_module)
            with tempfile.TemporaryDirectory() as temp_dir:
                image_path = Path(temp_dir) / "sample.png"
                image_path.write_text("x", encoding="utf-8")

                vs_module.optimize_images(str(image_path), {"optimize_images": False})

                self.assertTrue(image_path.exists())


if __name__ == "__main__":
    unittest.main()
