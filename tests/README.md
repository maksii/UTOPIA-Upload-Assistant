# Test Suite Overview

This directory contains unittest-based tests that exercise core upload flows, configuration validation, and tracker-specific logic. The suite uses realistic, fully mocked inputs for external services (MediaInfo, ffmpeg, TMDb, image hosts, torrent clients, and tracker endpoints) to keep runs deterministic while covering the same parsing and decision paths used in production.

## Structure and Coverage

### End-to-end flows
- `test_scenarios.py`: Runs three full upload scenarios (remux movie, web-dl hybrid movie, blu-ray TV series) through `do_the_thing`, including mocked MediaInfo, screenshots, uploads, torrents, and tracker processing.

### Media parsing and utilities
- `test_media_ffmpeg_screens.py`: Exercises MediaInfo export and ffmpeg-based frame parsing and fallback behavior.
- `test_torrentcreate_mkbrr.py`: Validates torrent creation logic for mkbrr and torf behavior.
- `test_args_region_tags.py`: Covers argument parsing, region/service detection, and tag extraction helpers.
- `unit/test_core_modules.py`: Covers comparison caching, overrides, bbcode cleanup, BDInfo comparison helpers, BTN errors, cleanup paths, and client ID parsing.
- `unit/test_disc_desc_utils.py`: Covers console helpers, cookie auth utilities, disc menus, disc parsing setup, dupe helpers, edition helpers, exceptions, MediaInfo utilities, and HTML to BBCode conversion.
- `unit/test_metadata_sources.py`: Covers disc size grouping, source detection, tracker cooldowns, season/episode helpers, IMDb safe lookup, scene attribute parsing, Blu-ray language parsing, manual package creation, metadata type coercion, and NFO creation.
- `unit/test_service_helpers.py`: Covers prep helpers, qBittorrent config validation, queue log handling, Radarr/Sonarr extractors, rehost helpers, search helpers, tracker modq checks, tracker meta image de-duplication, and TVDB helpers.
- `unit/test_video_helpers.py`: Covers TVMaze selection logic, type conversion helpers, video encode/uhd helpers, and VapourSynth optimization guard behavior.

### Configuration and tracker setup
- `test_configvalidator.py`: Validates config rules and error/warning behavior.
- `test_trackersetup.py`: Covers tracker definition and setup mapping behavior.
- `test_tracker_status_edges.py`: Covers tracker status decisions, naming prompts, dupes, and missing IDs.

### External services
- `test_tmdb.py`: Tests TMDb metadata flows and parsing.
- `test_uploadscreens.py`: Tests screenshot upload behavior and host response handling.

### Web UI and Docker entrypoints
- `test_webui_docker.py`: Covers web UI execution streaming and Docker entrypoint argument handling.

### Tracker-specific logic
- `test_tracker_specific.py`: Covers tracker-specific naming, mapping, and additional checks for AITHER, LST, UTP, and HUNO.

### Edge cases
- `test_edge_cases.py`: Validates missing file path handling, ffmpeg errors, manual edition/tag overrides, missing IDs, trumpable dupe logic, bloat audio checks, and torrent client injection.

## How to Run

From the repository root:

```bash
ruff check .
ruff format .
make test
```

The `make test` target runs `python -m unittest discover -s tests -p "test_*.py"`.

Some environments lack optional third-party dependencies; the tests include lightweight stubs in `tests/` for those modules.

## Extending the Suite

- Add new scenario variants in `test_scenarios.py` by extending the `MediaInfoSpec` and `Scenario` fixtures.
- Add tracker-specific branches in `test_tracker_specific.py` when new trackers or rules are introduced.
- Keep external calls mocked with realistic payloads; avoid adding tests that do not cover meaningful logic.

## Currently Covered

- Full mocked upload flows for three representative scenarios.
- BluRay remux and BluRay encode flows in the scenario suite.
- MediaInfo parsing, ffmpeg frame inspection, screenshot upload, TMDb metadata retrieval, torrent creation, and tracker processing.
- Config validation and tracker setup rules.
- Tracker-specific naming and mapping for AITHER, LST, UTP, and HUNO.
- Edge cases for missing files, missing IDs, bloat audio rules, and trumpable dupes.
- Web UI execution and Docker entrypoint defaults.

## Known Gaps / Not Covered Yet

- Disc formats beyond Blu-ray (e.g., DVD/HDDVD) through full end-to-end flows.
- Cross-seed workflows and multi-tracker claim flows beyond the mocked scenarios.
- Real network error handling for tracker uploads and image rehosts (kept mocked for determinism).
- Web UI validation uses a mocked subprocess; it does not exercise real-time output streaming from a live upload process.
- Performance and concurrency stress tests.

## Coverage Snapshot

- Core utilities and helpers are covered via `tests/unit/` and focused unit tests.
- End-to-end flows cover the upload pipeline, media parsing, screenshots, torrents, and tracker interactions.
- Scenario and edge-case suites cover missing IDs, duplicate rules, bloat audio checks, and tracker naming behavior.

### Module-level gaps still called out for expansion
- Cookie auth refresh and login workflows.
- Disc parsing playlists and full BD summary logic.
- Description builder formatting beyond HTML-to-BBCode.
- Tracker metadata extraction, serialization, and handle orchestration.
- TVDB flows and metadata selection logic.
- Video validation, search filesystem traversal, and rehost host-mapping rules.
