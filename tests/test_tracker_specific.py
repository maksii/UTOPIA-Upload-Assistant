import unittest
from typing import Any

from src.trackers.AITHER import AITHER
from src.trackers.HUNO import HUNO
from src.trackers.LST import LST
from src.trackers.UTP import UTP


class AitherTrackerTests(unittest.IsolatedAsyncioTestCase):
    async def test_additional_checks_require_valid_mediainfo(self) -> None:
        tracker = AITHER({"TRACKERS": {"AITHER": {}}})
        meta = {"valid_mi": False}

        result = await tracker.get_additional_checks(meta)

        self.assertFalse(result)

    async def test_get_name_adds_foreign_language_for_non_english(self) -> None:
        tracker = AITHER({"TRACKERS": {"AITHER": {}}})
        meta = {
            "name": "Sample Film 2024 1080p BluRay REMUX AVC FLAC 2.0-FAKE",
            "year": "2024",
            "resolution": "1080p",
            "type": "REMUX",
            "source": "BluRay",
            "video_codec": "AVC",
            "video_encode": "H.264",
            "audio": "FLAC 2.0",
            "is_disc": "",
            "language_checked": True,
            "audio_languages": ["Japanese"],
        }

        renamed = await tracker.get_name(meta)

        self.assertIn("JAPANESE 1080p", renamed["name"])

    async def test_get_name_for_dvdrip_updates_tokens(self) -> None:
        tracker = AITHER({"TRACKERS": {"AITHER": {}}})
        meta = {
            "name": "Sample Film 2024 DVD H.264 AAC 2.0-FAKE",
            "year": "2024",
            "resolution": "480p",
            "type": "DVDRIP",
            "source": "DVD",
            "video_codec": "H.264",
            "video_encode": "x264",
            "audio": "AAC 2.0",
            "is_disc": "",
            "language_checked": True,
            "audio_languages": ["English"],
        }

        renamed = await tracker.get_name(meta)

        self.assertIn("AAC 2.0x264", renamed["name"])
        self.assertIn("Sample Film", renamed["name"])


class LstTrackerTests(unittest.IsolatedAsyncioTestCase):
    async def test_additional_checks_require_encoding_settings(self) -> None:
        tracker = LST({"TRACKERS": {"LST": {}}})
        meta = {"valid_mi_settings": False}

        result = await tracker.get_additional_checks(meta)

        self.assertFalse(result)

    async def test_get_type_id_maps_dvdrip(self) -> None:
        tracker = LST({"TRACKERS": {"LST": {}}})
        meta = {"type": "DVDRIP"}

        result = await tracker.get_type_id(meta)

        self.assertEqual(result["type_id"], "3")

    async def test_get_additional_data_includes_edition(self) -> None:
        tracker = LST({"TRACKERS": {"LST": {}}})
        meta = {"edition": "Director's Cut"}

        result = await tracker.get_additional_data(meta)

        self.assertEqual(result["edition_id"], 2)

    async def test_get_name_for_tv_dvdrip(self) -> None:
        tracker = LST({"TRACKERS": {"LST": {}}})
        meta = {
            "category": "TV",
            "name": "Series Title DVD AVC-FAKE",
            "resolution": "576p",
            "video_encode": "x264",
            "type": "DVDRIP",
            "source": "DVD",
            "audio": "AAC 2.0",
            "video_codec": "AVC",
        }

        renamed = await tracker.get_name(meta)

        self.assertIn("576p", renamed["name"])
        self.assertIn("AAC 2.0 AVC", renamed["name"])


class UtpTrackerTests(unittest.IsolatedAsyncioTestCase):
    async def test_category_id_switches_to_fanres(self) -> None:
        tracker = UTP({"TRACKERS": {"UTP": {}}})
        meta = {"category": "MOVIE", "edition": "FANRES"}

        result = await tracker.get_category_id(meta)

        self.assertEqual(result["category_id"], "3")

    async def test_resolution_id_maps_2160p(self) -> None:
        tracker = UTP({"TRACKERS": {"UTP": {}}})
        meta = {"resolution": "2160p"}

        result = await tracker.get_resolution_id(meta)

        self.assertEqual(result["resolution_id"], "2")


class HunoTrackerTests(unittest.IsolatedAsyncioTestCase):
    async def test_additional_checks_require_hevc_for_encodes(self) -> None:
        tracker = HUNO({"TRACKERS": {"HUNO": {}}})
        meta = {
            "audio": "AAC 2.0",
            "audio_languages": ["English"],
            "language_checked": True,
            "type": "ENCODE",
            "video_codec": "AVC",
            "unattended": True,
            "valid_mi_settings": True,
        }

        result = await tracker.get_additional_checks(meta)

        self.assertFalse(result)

    async def test_additional_checks_rejects_high_crf(self) -> None:
        tracker = HUNO({"TRACKERS": {"HUNO": {}}})
        meta = {
            "audio": "AAC 2.0",
            "audio_languages": ["English"],
            "language_checked": True,
            "type": "ENCODE",
            "video_codec": "HEVC",
            "unattended": True,
            "valid_mi_settings": True,
            "is_disc": False,
            "mediainfo": {"media": {"track": [{"@type": "Video", "Encoded_Library_Settings": "crf=24", "BitRate": "4000000"}]}},
            "genre": "",
        }

        result = await tracker.get_additional_checks(meta)

        self.assertFalse(result)

    async def test_get_name_sets_nogroup_for_invalid_tag(self) -> None:
        tracker = HUNO({"TRACKERS": {"HUNO": {}}})
        meta: dict[str, Any] = {
            "category": "MOVIE",
            "title": "Skyward",
            "year": "2022",
            "type": "WEBDL",
            "resolution": "1080p",
            "audio": "AAC 2.0",
            "audio_languages": ["English"],
            "language_checked": True,
            "service": "NF",
            "video_encode": "H.264",
            "video_codec": "AVC",
            "source": "WEB-DL",
            "hdr": "",
            "tag": "-NoGrp",
            "repack": "",
            "edition": "",
            "season": "",
            "episode": "",
            "3D": "",
            "region": "",
            "hardcoded_subs": False,
            "is_disc": "",
            "webdv": "",
            "dvd_size": "",
            "distributor": "",
            "hfr": "",
            "filelist": ["Skyward.2022.1080p.WEB-DL.H.264-NoGrp.mkv"],
            "path": "Skyward.2022.1080p.WEB-DL.H.264-NoGrp.mkv",
        }

        renamed = await tracker.get_name(meta)

        self.assertIn("NOGRP", renamed["name"])

    async def test_get_audio_reports_multi_language(self) -> None:
        tracker = HUNO({"TRACKERS": {"HUNO": {}}})
        meta = {
            "audio": "DDP 5.1",
            "channels": "5.1",
            "audio_languages": ["English", "German", "French"],
            "language_checked": True,
        }

        result = await tracker.get_audio(meta)

        self.assertIn("Multi", result)


if __name__ == "__main__":
    unittest.main()
