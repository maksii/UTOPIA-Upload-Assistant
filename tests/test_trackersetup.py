import unittest

from src import trackersetup


class TrackerSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "TRACKERS": {
                "default_trackers": "PTP, HDB, UNKNOWN",
                "PTP": {"api_key": "fake_ptp_key"},
                "HDB": {"api_key": "fake_hdb_key"},
            }
        }

    def test_trackers_enabled_respects_manual_and_filters_unknown(self) -> None:
        setup = trackersetup.TRACKER_SETUP(self.config)
        meta = {"trackers": ["PTP", "UNKNOWN"], "manual": True}

        enabled = setup.trackers_enabled(meta)

        self.assertIn("MANUAL", enabled)
        self.assertIn("PTP", enabled)
        self.assertNotIn("UNKNOWN", enabled)

    def test_trackers_enabled_uses_default_trackers(self) -> None:
        setup = trackersetup.TRACKER_SETUP(self.config)
        meta = {"trackers": None, "manual": False}

        enabled = setup.trackers_enabled(meta)

        self.assertIn("PTP", enabled)
        self.assertIn("HDB", enabled)
        self.assertNotIn("UNKNOWN", enabled)

    def test_tracker_definitions_cover_sets(self) -> None:
        tracker_keys = set(trackersetup.tracker_class_map.keys())

        self.assertTrue(trackersetup.api_trackers.issubset(tracker_keys))
        self.assertTrue(trackersetup.http_trackers.issubset(tracker_keys))
        self.assertTrue(trackersetup.other_api_trackers.issubset(tracker_keys))


if __name__ == "__main__":
    unittest.main()
