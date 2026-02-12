import unittest

from src import configvalidator


class ConfigValidatorTests(unittest.TestCase):
    def test_validate_config_happy_path(self) -> None:
        config = {
            "DEFAULT": {
                "tmdb_api": "fake_tmdb_key",
                "img_host_1": "imgbb",
                "imgbb_api": "fake_imgbb_key",
                "screens": "6",
            },
            "TRACKERS": {
                "default_trackers": "PTP, HDB",
                "PTP": {"api_key": "fake_ptp_key"},
                "HDB": {"api_key": "fake_hdb_key"},
            },
        }

        is_valid, errors, warnings = configvalidator.validate_config(config)

        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_validate_config_reports_errors_and_warnings(self) -> None:
        config = {
            "DEFAULT": {
                "tmdb_api": "",
                "img_host_1": "unknown_host",
                "screens": "not-a-number",
                "ffmpeg_compression": object(),
            },
            "TRACKERS": {
                "default_trackers": ["PTP"],
                "PTP": "not-a-dict",
            },
        }

        is_valid, errors, warnings = configvalidator.validate_config(config)

        self.assertFalse(is_valid)
        self.assertTrue(any("tmdb_api" in error for error in errors))
        warning_messages = [str(warning) for warning in warnings]
        self.assertTrue(any("Unknown image host" in warning for warning in warning_messages))
        self.assertTrue(any("Cannot parse" in warning for warning in warning_messages))
        self.assertTrue(any("Tracker config must be a dictionary" in warning for warning in warning_messages))


if __name__ == "__main__":
    unittest.main()
