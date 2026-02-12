# Test Suite Overview

This directory contains unittest-based tests that exercise core upload flows, configuration validation, and tracker-specific logic. The suite uses realistic, fully mocked inputs for external services (MediaInfo, ffmpeg, TMDb, image hosts, torrent clients, and tracker endpoints) to keep runs deterministic while covering the same parsing and decision paths used in production.

## Structure and Coverage

### Shared infrastructure
- **`conftest.py`**: Shared fixtures and helpers. Defines `FakeFFmpegCommand`, `FakeResponse`, `FakeAsyncClient`, `FakeTracker`, `FakeTrackerSetup`, `FakeTrackerStatusManager`, `FakeDupeTracker`, plus factory helpers `make_meta()`, `make_config()`, and `tmp_config()`. Import from `tests.conftest` in test files.
- **`_stubs/`**: Optional dependency stubs (aiohttp, flask, cli_ui, etc.) for environments that do not install all third-party packages. Stubs are not on `sys.path` by default; use real packages when installed. For minimal installs, prepend `tests/_stubs` to `sys.path` before running tests.

### End-to-end flows
- `test_scenarios.py`: Runs four full upload scenarios (remux, web-dl hybrid, blu-ray TV, blu-ray encode) through `do_the_thing` via the **ScenarioRunner** helper, which encapsulates all mocks and the ExitStack. Add new variants by defining a `MediaInfoSpec` and `Scenario` and calling `_run_upload_flow(scenario)`.

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
make test
```

Or directly:

```bash
python -m pytest tests/ -v
```

Run with coverage:

```bash
make coverage
# or: python -m pytest tests/ --cov=src --cov-report=term-missing
```

Lint (includes test code):

```bash
make lint
# or: ruff check . && ruff format --check .
```

Pytest is configured in `pyproject.toml` (`[tool.pytest.ini_options]`). The suite is compatible with both `pytest` and `python -m unittest discover -s tests -p "test_*.py"`.

## Extending the Suite

- **New scenario**: In `test_scenarios.py`, define a `MediaInfoSpec` and `Scenario`, then call `await self._run_upload_flow(scenario)`. The **ScenarioRunner** in that file holds all mocks; extend it if you need new patched behavior.
- **New tracker tests**: Add cases in `test_tracker_specific.py`; use `make_config()` and `make_meta()` from `tests.conftest` for minimal config/meta dicts.
- **Shared fakes**: Import `FakeTracker`, `FakeResponse`, etc. from `tests.conftest`; add new shared fakes in `conftest.py` when multiple test files need the same stub.
- Keep external calls mocked with realistic payloads; avoid adding tests that do not cover meaningful logic.

## Currently Covered

- Full mocked upload flows for four representative scenarios (remux, web-dl, blu-ray TV, blu-ray encode).
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

## Coverage

- Run `make coverage` (or `pytest tests/ --cov=src --cov-report=term-missing`) to report line coverage for `src/`.
- Core utilities and helpers are covered via `tests/unit/` and focused unit tests.
- End-to-end flows cover the upload pipeline, media parsing, screenshots, torrents, and tracker interactions.

### Module-level gaps still called out for expansion
- Cookie auth refresh and login workflows.
- Disc parsing playlists and full BD summary logic.
- Description builder formatting beyond HTML-to-BBCode.
- Tracker metadata extraction, serialization, and handle orchestration.
- TVDB flows and metadata selection logic.
- Video validation, search filesystem traversal, and rehost host-mapping rules.
