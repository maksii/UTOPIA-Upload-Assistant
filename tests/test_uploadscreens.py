import asyncio
import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.uploadscreens import upload_image_task
from tests.conftest import FakeAsyncClient, FakeResponse


class UploadScreensTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_image_task_ptpimg(self) -> None:
        response = FakeResponse([{"code": "abc123", "ext": "png"}], status_code=200)
        fake_client = FakeAsyncClient(post_response=response)
        config = {"DEFAULT": {"ptpimg_api": "fake_key"}}
        meta = {"debug": False}

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, "screen.png")
            await asyncio.to_thread(Path(image_path).write_bytes, b"fake image")

            with mock.patch("src.uploadscreens.httpx.AsyncClient", return_value=fake_client):
                result = await upload_image_task([image_path, "ptpimg", config, meta])

        self.assertEqual(result["status"], "success")
        self.assertIn("img_url", result)
        self.assertTrue(result["img_url"].startswith("https://ptpimg.me/"))

    async def test_upload_image_task_imgbb(self) -> None:
        payload = {
            "success": True,
            "data": {
                "medium": {"url": "https://imgbb.com/medium.png"},
                "thumb": {"url": "https://imgbb.com/thumb.png"},
                "image": {"url": "https://imgbb.com/raw.png"},
                "url_viewer": "https://imgbb.com/viewer",
            },
        }
        response = FakeResponse(payload, status_code=200)
        fake_client = FakeAsyncClient(post_response=response)
        config = {"DEFAULT": {"imgbb_api": "fake_key"}}
        meta = {"debug": False}

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, "screen.png")
            await asyncio.to_thread(Path(image_path).write_bytes, base64.b64decode(base64.b64encode(b"fake image")))

            with mock.patch("src.uploadscreens.httpx.AsyncClient", return_value=fake_client):
                result = await upload_image_task([image_path, "imgbb", config, meta])

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["img_url"], "https://imgbb.com/medium.png")
        self.assertEqual(result["raw_url"], "https://imgbb.com/raw.png")
        self.assertEqual(result["web_url"], "https://imgbb.com/viewer")


if __name__ == "__main__":
    unittest.main()
