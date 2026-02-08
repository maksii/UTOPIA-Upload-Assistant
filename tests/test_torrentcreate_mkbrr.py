import asyncio
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.torrentcreate import TorrentCreator, calculate_piece_size


class FakePopen:
    def __init__(self, cmd, stdout, stderr, text, bufsize):
        _ = (cmd, stdout, stderr, text, bufsize)
        output = "Hashing pieces [1.2 MiB/s] 10% [5s:45s]\nWrote /tmp/fake.torrent\n"
        self.stdout = io.StringIO(output)

    def wait(self) -> int:
        return 0


class TorrentCreateTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_torrent_with_mkbrr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = temp_dir
            uuid = "scenario"
            tmp_dir = os.path.join(base_dir, "tmp", uuid)
            os.makedirs(tmp_dir, exist_ok=True)

            input_path = os.path.join(base_dir, "Sample.Movie.2024.mkv")
            await asyncio.to_thread(Path(input_path).write_bytes, b"fake movie data")

            mkbrr_path = os.path.join(base_dir, "bin", "mkbrr", "linux", "amd64", "mkbrr")
            os.makedirs(os.path.dirname(mkbrr_path), exist_ok=True)
            await asyncio.to_thread(Path(mkbrr_path).write_bytes, b"#!/bin/sh\n")

            output_filename = "Sample.Movie.2024"
            output_path = os.path.join(tmp_dir, f"{output_filename}.torrent")
            await asyncio.to_thread(Path(output_path).write_bytes, b"")

            meta = {
                "base_dir": base_dir,
                "uuid": uuid,
                "mkbrr": True,
                "mkbrr_threads": "4",
                "randomized": 0,
                "keep_folder": False,
                "isdir": False,
                "is_disc": False,
                "filelist": [input_path],
                "trackers": ["PTP"],
                "debug": True,
            }

            with mock.patch("src.torrentcreate.subprocess.Popen", FakePopen), mock.patch("src.torrentcreate.TorrentCreator.get_mkbrr_path", return_value=mkbrr_path):
                torrent_path = await TorrentCreator.create_torrent(
                    meta=meta,
                    path=input_path,
                    output_filename=output_filename,
                )

            self.assertEqual(torrent_path, output_path)
            self.assertTrue(os.path.exists(torrent_path))

    def test_calculate_piece_size_caps_for_hdb(self) -> None:
        meta = {"trackers": ["HDB"], "debug": False}
        total_size = 120 * 1024 * 1024 * 1024

        piece_size = calculate_piece_size(total_size, 32 * 1024, 128 * 1024 * 1024, meta)

        self.assertLessEqual(piece_size, 16 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
