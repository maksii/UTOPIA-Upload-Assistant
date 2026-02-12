import unittest

from src.args import Args
from src.region import get_region, get_service
from src.tags import get_tag


class ArgsParsingTests(unittest.TestCase):
    def test_parse_tmdb_id_from_url(self) -> None:
        args = Args({"DEFAULT": {"screens": 3}})

        category, tmdb_id = args.parse_tmdb_id("https://www.themoviedb.org/movie/12345", None)

        self.assertEqual(category, "MOVIE")
        self.assertEqual(tmdb_id, 12345)

    def test_parse_tmdb_id_from_prefixed_value(self) -> None:
        args = Args({"DEFAULT": {"screens": 3}})

        category, tmdb_id = args.parse_tmdb_id("tv/6789", "MOVIE")

        self.assertEqual(category, "TV")
        self.assertEqual(tmdb_id, 6789)


class RegionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_region_override(self) -> None:
        region = await get_region({"label": "Example Release"}, region="usa")

        self.assertEqual(region, "USA")

    async def test_region_detects_from_label(self) -> None:
        region = await get_region({"label": "Sample Release USA BluRay"})

        self.assertEqual(region, "USA")

    async def test_service_detection(self) -> None:
        service, longname = await get_service("Sample.Show.2024.NF.WEB-DL.mkv", tag="-FAKE", audio="AAC 2.0")

        self.assertEqual(service, "NF")
        self.assertTrue(longname)


class TagDetectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_tag_detects_release_group(self) -> None:
        meta = {"anime": False, "is_disc": "", "debug": False, "scene": False}

        tag = await get_tag("Sample.Movie.2024.1080p.WEB-DL.H.264-FAKE.mkv", meta)

        self.assertEqual(tag, "-FAKE")

    async def test_tag_detects_anime_group(self) -> None:
        meta = {"anime": True, "is_disc": "", "debug": False, "scene": False}

        tag = await get_tag("[FAKE] Sample Anime - 01.mkv", meta)

        self.assertEqual(tag, "-FAKE")


if __name__ == "__main__":
    unittest.main()
