import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import exportmi, takescreens


class FakeFFmpegCommand:
    def __init__(self) -> None:
        self._cmd = ["ffmpeg", "-i", "input", "-filter", "showinfo"]

    def __getitem__(self, _key: str) -> "FakeFFmpegCommand":
        return self

    def filter(self, _name: str) -> "FakeFFmpegCommand":
        return self

    def output(self, *_args, **_kwargs) -> "FakeFFmpegCommand":
        return self

    def global_args(self, *_args) -> "FakeFFmpegCommand":
        return self

    def compile(self) -> list[str]:
        return self._cmd


class MediaInfoAndScreensTests(unittest.IsolatedAsyncioTestCase):
    async def test_export_info_uses_mediainfo_parse(self) -> None:
        fake_text = "General\nReportBy Fake\nFormat : Matroska\n"
        fake_json = json.dumps({"media": {"@ref": "", "track": [{"@type": "General", "UniqueID": "1"}]}})

        def fake_parse(_path: str, output: str = "STRING", full: bool = False):
            _ = full
            return fake_text if output == "STRING" else fake_json

        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = temp_dir
            folder_id = "media"
            os.makedirs(os.path.join(base_dir, "tmp", folder_id), exist_ok=True)
            video_path = os.path.join(base_dir, "Sample.Movie.2024.mkv")
            await asyncio.to_thread(Path(video_path).write_bytes, b"fake movie")

            with mock.patch("src.exportmi.MediaInfo.parse", side_effect=fake_parse), mock.patch("src.exportmi.setup_mediainfo_library", return_value=None):
                mi = await exportmi.exportInfo(
                    video=video_path,
                    isdir=False,
                    folder_id=folder_id,
                    base_dir=base_dir,
                    is_dvd=False,
                    debug=False,
                )

            self.assertIn("media", mi)
            mediainfo_txt = os.path.join(base_dir, "tmp", folder_id, "MEDIAINFO.txt")
            contents = await asyncio.to_thread(Path(mediainfo_txt).read_text, encoding="utf-8")
            self.assertNotIn("ReportBy", contents)

    async def test_get_frame_info_parses_ffmpeg_output(self) -> None:
        stderr = b"[Parsed_showinfo] n:1 pict_type:I pts_time:1.500"

        async def fake_run_ffmpeg(_command):
            return 0, b"", stderr

        fake_ffmpeg = mock.Mock()
        fake_ffmpeg.input.return_value = FakeFFmpegCommand()

        with mock.patch("src.takescreens.run_ffmpeg", side_effect=fake_run_ffmpeg), mock.patch("src.takescreens.ffmpeg", fake_ffmpeg):
            meta = {"frame_rate": 24.0, "debug": False}
            info = await takescreens.get_frame_info("video.mkv", 1.5, meta)

        self.assertEqual(info["frame_type"], "I")
        self.assertEqual(info["frame_number"], 36)
        self.assertEqual(info["pts_time"], 1.5)

    async def test_get_frame_info_falls_back_on_error(self) -> None:
        async def fake_run_ffmpeg(_command):
            return None, b"", b""

        fake_ffmpeg = mock.Mock()
        fake_ffmpeg.input.return_value = FakeFFmpegCommand()

        with mock.patch("src.takescreens.run_ffmpeg", side_effect=fake_run_ffmpeg), mock.patch("src.takescreens.ffmpeg", fake_ffmpeg):
            meta = {"frame_rate": 30.0, "debug": False}
            info = await takescreens.get_frame_info("video.mkv", 2.0, meta)

        self.assertEqual(info["frame_type"], "Unknown")
        self.assertEqual(info["frame_number"], 60)


if __name__ == "__main__":
    unittest.main()
