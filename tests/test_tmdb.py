import unittest
from unittest import mock

from src.tmdb import TmdbManager
from tests.conftest import FakeAsyncClient


class TmdbTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_tmdb_from_imdb_movie(self) -> None:
        config = {"DEFAULT": {"tmdb_api": "fake_key"}}
        manager = TmdbManager(config)
        payload = {"movie_results": [{"id": 12345, "original_language": "en"}], "tv_results": []}
        fake_client = FakeAsyncClient(get_payload=payload)

        with mock.patch("src.tmdb.httpx.AsyncClient", return_value=fake_client):
            category, tmdb_id, original_language, filename_search = await manager.get_tmdb_from_imdb("tt1234567")

        self.assertEqual(category, "MOVIE")
        self.assertEqual(tmdb_id, 12345)
        self.assertEqual(original_language, "en")
        self.assertFalse(filename_search)

    async def test_get_tmdb_from_imdb_tv_preference(self) -> None:
        config = {"DEFAULT": {"tmdb_api": "fake_key"}}
        manager = TmdbManager(config)
        payload = {
            "movie_results": [{"id": 111, "original_language": "en"}],
            "tv_results": [{"id": 222, "original_language": "ja"}],
        }
        fake_client = FakeAsyncClient(get_payload=payload)

        with mock.patch("src.tmdb.httpx.AsyncClient", return_value=fake_client):
            category, tmdb_id, original_language, filename_search = await manager.get_tmdb_from_imdb(
                "tt7654321",
                category_preference="TV",
            )

        self.assertEqual(category, "TV")
        self.assertEqual(tmdb_id, 222)
        self.assertEqual(original_language, "ja")
        self.assertFalse(filename_search)


if __name__ == "__main__":
    unittest.main()
