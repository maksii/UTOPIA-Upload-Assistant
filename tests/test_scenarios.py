import asyncio
import importlib
import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import Any, Optional
from unittest import mock

from src import exportmi


@dataclass(frozen=True)
class AudioTrack:
    language: str
    codec: str
    channels: str
    bitrate_kbps: int
    title: str
    default: bool = False


@dataclass(frozen=True)
class SubtitleTrack:
    language: str
    codec: str
    title: str
    forced: bool = False


@dataclass(frozen=True)
class MediaInfoSpec:
    title: str
    year: int
    source: str
    resolution: str
    video_codec: str
    bit_depth: int
    frame_rate: str
    duration: str
    file_size_gib: float
    audio_tracks: list[AudioTrack]
    subtitle_tracks: list[SubtitleTrack]
    tags: list[str]
    group: str
    dual_audio: bool = False
    season: Optional[int] = None

    def release_name(self) -> str:
        title = self.title.replace(" ", ".")
        parts = [title, str(self.year)]
        if self.season is not None:
            parts.append(f"S{self.season:02d}")
        parts.extend([self.resolution, self.source])
        parts.extend(self.tags)
        if self.dual_audio:
            parts.append("DUAL")
        if self.video_codec not in self.tags:
            parts.append(self.video_codec)
        return ".".join(parts) + f"-{self.group}"


@dataclass(frozen=True)
class Scenario:
    category: str
    tracker: str
    is_disc: bool
    tmdb_id: int
    imdb_id: int
    tvdb_id: int
    mediainfo: MediaInfoSpec


class FakeTracker:
    approved_image_hosts = ["imgbb"]
    torrent_url = "https://tracker.example/torrents/"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def check_image_hosts(self, _meta: dict[str, Any]) -> None:
        return None


class FakeTrackerStatusManager:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def process_all_trackers(self, meta: dict[str, Any]) -> int:
        meta["tracker_status"] = {tracker: {"upload": True, "status_message": "OK", "torrent_id": 123} for tracker in meta.get("trackers", [])}
        return len(meta.get("trackers", []))


def _write_config(base_dir: Path) -> Path:
    config_path = base_dir / "data" / "config.py"
    config_content = {
        "DEFAULT": {
            "tmdb_api": "fake_tmdb_key",
            "img_host_1": "imgbb",
            "imgbb_api": "fake_imgbb_key",
            "screens": "3",
            "mkbrr": True,
            "mkbrr_threads": "4",
            "tracker_pass_checks": 1,
            "min_successful_image_uploads": 2,
            "cross_seeding": False,
            "search_requests": False,
        },
        "TRACKERS": {
            "default_trackers": "PTP",
            "PTP": {"api_key": "fake_ptp_key"},
        },
    }
    config_path.write_text(f"config = {pformat(config_content)}\n", encoding="utf-8")
    return config_path


def _human_size_gib(value: float) -> str:
    return f"{value:.2f} GiB"


def _audio_title(track: AudioTrack) -> str:
    return f"{track.language} | {track.codec} | {track.channels} | {track.bitrate_kbps} kbps | {track.title}"


def _subtitle_title(track: SubtitleTrack) -> str:
    forced = " | Forced" if track.forced else ""
    return f"{track.language} | {track.title}{forced}"


def _mediainfo_text(spec: MediaInfoSpec) -> str:
    width_map = {"1080p": "1 920", "2160p": "3 840"}
    height_map = {"1080p": "1 080", "2160p": "2 160"}
    width = width_map.get(spec.resolution, "1 920")
    height = height_map.get(spec.resolution, "1 080")
    codec_id = "V_MPEG4/ISO/AVC" if spec.video_codec == "AVC" else "V_MPEGH/ISO/HEVC"
    lines = [
        "General",
        f"Unique ID                                : {abs(hash(spec.release_name())):x}",
        f"Complete name                            : {spec.release_name()}.mkv",
        "Format                                   : Matroska",
        "Format version                           : Version 4",
        f"File size                                : {_human_size_gib(spec.file_size_gib)}",
        f"Duration                                 : {spec.duration}",
        "Overall bit rate mode                    : Variable",
        "Overall bit rate                         : 24.0 Mb/s",
        f"Frame rate                               : {spec.frame_rate} FPS",
        f"Movie name                               : {spec.title}",
        "Encoded date                             : 2027-01-02 12:00:00 UTC",
        "Writing application                      : mkvmerge v96.0 ('It's My Life') 64-bit",
        "Writing library                          : libebml v1.4.5 + libmatroska v1.7.1",
        "Attachments                              : cover.jpg",
        "",
        "Video",
        "ID                                       : 1",
        f"Format                                   : {spec.video_codec}",
        f"Format/Info                              : {spec.video_codec}",
        "Format profile                           : High@L4.1",
        "Format settings                          : CABAC / 4 Ref Frames",
        f"Codec ID                                 : {codec_id}",
        f"Duration                                 : {spec.duration}",
        "Bit rate mode                            : Variable",
        "Bit rate                                 : 18.0 Mb/s",
        f"Width                                    : {width} pixels",
        f"Height                                   : {height} pixels",
        "Display aspect ratio                     : 16:9",
        "Frame rate mode                          : Constant",
        f"Frame rate                               : {spec.frame_rate} FPS",
        "Color space                              : YUV",
        "Chroma subsampling                       : 4:2:0",
        f"Bit depth                                : {spec.bit_depth} bits",
        "Scan type                                : Progressive",
        "Bits/(Pixel*Frame)                       : 0.274",
        "Stream size                              : 7.67 GiB (60%)",
        "Language                                 : English",
        "Default                                  : No",
        "Forced                                   : No",
        "",
    ]

    for index, track in enumerate(spec.audio_tracks, start=1):
        lines.extend(
            [
                f"Audio #{index}",
                f"ID                                       : {index + 1}",
                f"Format                                   : {track.codec}",
                f"Format/Info                              : {track.codec}",
                "Codec ID                                 : A_AC3"
                if "AC-3" in track.codec
                else "Codec ID                                 : A_EAC3"
                if "E-AC-3" in track.codec
                else "Codec ID                                 : A_TRUEHD"
                if "TrueHD" in track.codec
                else "Codec ID                                 : A_AAC-2"
                if "AAC" in track.codec
                else "Codec ID                                 : A_FLAC",
                f"Duration                                 : {spec.duration}",
                "Bit rate mode                            : Constant",
                f"Bit rate                                 : {track.bitrate_kbps} kb/s",
                f"Channel(s)                               : {track.channels} channels",
                "Sampling rate                            : 48.0 kHz",
                "Compression mode                         : Lossy" if track.codec in {"AAC", "AC-3", "E-AC-3"} else "Compression mode                         : Lossless",
                "Stream size                              : 369 MiB (3%)",
                f"Title                                    : {_audio_title(track)}",
                f"Language                                 : {track.language}",
                "Default                                  : Yes" if track.default else "Default                                  : No",
                "Forced                                   : No",
                "",
            ]
        )

    for index, track in enumerate(spec.subtitle_tracks, start=1):
        lines.extend(
            [
                f"Text #{index}",
                f"ID                                       : {index + 10}",
                f"Format                                   : {track.codec}",
                "Codec ID                                 : S_TEXT/UTF8" if track.codec == "UTF-8" else "Codec ID                                 : S_TEXT/ASS",
                f"Duration                                 : {spec.duration}",
                "Bit rate                                 : 40 b/s",
                "Frame rate                               : 0.150 FPS",
                "Count of elements                        : 650",
                "Stream size                              : 21.4 KiB (0%)",
                f"Title                                    : {_subtitle_title(track)}",
                f"Language                                 : {track.language}",
                "Default                                  : No",
                f"Forced                                   : {'Yes' if track.forced else 'No'}",
                "",
            ]
        )

    lines.extend(
        [
            "Menu",
            "00:00:00.000                             : en:Chapter 01",
            "00:07:22.875                             : en:Chapter 02",
            "00:18:49.625                             : en:Chapter 03",
            "00:28:14.458                             : en:Chapter 04",
            "00:38:08.041                             : en:Chapter 05",
            "00:49:34.166                             : en:Chapter 06",
        ]
    )

    return "\n".join(lines)


def _mediainfo_json(spec: MediaInfoSpec) -> dict[str, Any]:
    audio_tracks = [
        {
            "@type": "Audio",
            "Format": track.codec,
            "Channels": track.channels,
            "Language": track.language[:2].lower(),
            "BitRate": str(track.bitrate_kbps * 1000),
            "Title": _audio_title(track),
        }
        for track in spec.audio_tracks
    ]
    subtitle_tracks = [
        {
            "@type": "Text",
            "Format": track.codec,
            "Language": track.language[:2].lower(),
            "Title": _subtitle_title(track),
        }
        for track in spec.subtitle_tracks
    ]
    video_width = "3840" if spec.resolution == "2160p" else "1920"
    video_height = "2160" if spec.resolution == "2160p" else "1080"
    return {
        "media": {
            "@ref": f"{spec.release_name()}.mkv",
            "track": [
                {
                    "@type": "General",
                    "UniqueID": str(abs(hash(spec.release_name()))),
                    "VideoCount": "1",
                    "AudioCount": str(len(spec.audio_tracks)),
                    "TextCount": str(len(spec.subtitle_tracks)),
                    "Format": "Matroska",
                    "FileSize": str(int(spec.file_size_gib * 1024 * 1024 * 1024)),
                    "Duration": "4800.000",
                },
                {
                    "@type": "Video",
                    "Format": spec.video_codec,
                    "Format_Profile": "High@L4.1",
                    "Width": video_width,
                    "Height": video_height,
                    "FrameRate": spec.frame_rate,
                    "BitRate": "18000000",
                    "Language": "en",
                },
                *audio_tracks,
                *subtitle_tracks,
            ],
        }
    }


class UploadScenarioTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_dir = Path(__file__).resolve().parents[1]
        cls.config_path = cls.base_dir / "data" / "config.py"
        cls.original_config = cls.config_path.read_text(encoding="utf-8") if cls.config_path.exists() else None
        _write_config(cls.base_dir)
        if "upload" in sys.modules:
            del sys.modules["upload"]
        import upload

        cls.upload = importlib.reload(upload)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.original_config is None:
            if cls.config_path.exists():
                cls.config_path.unlink()
        else:
            cls.config_path.write_text(cls.original_config, encoding="utf-8")

    async def _run_upload_flow(self, scenario: Scenario) -> None:
        upload = self.upload
        tracker_map = {scenario.tracker: FakeTracker}
        captured_meta: list[dict[str, Any]] = []

        async def fake_update_notification(_base_dir: str) -> str:
            return "v0.0.0"

        async def fake_get_mkbrr_path(_meta: dict[str, Any], _base_dir: Optional[str] = None) -> str:
            return "/tmp/fake-mkbrr"

        async def fake_handle_queue(_path: str, _meta: dict[str, Any], _paths: list[str], _base_dir: str):
            return [_path], None

        async def fake_gather_prep(_self, meta: dict[str, Any], mode: str) -> dict[str, Any]:
            _ = mode
            meta["screens"] = 3
            meta["cutoff"] = 1
            meta["imghost"] = "imgbb"
            meta["unattended"] = True
            meta["unattended_confirm"] = True
            meta["keep_images"] = True
            meta["category"] = scenario.category
            meta["is_disc"] = "BDMV" if scenario.is_disc else False
            meta["trackers"] = [scenario.tracker]
            meta["trackers_remove"] = None
            meta["manual_frames"] = ""
            meta["comparison"] = False
            meta["skip_imghost_upload"] = False
            meta["ffdebug"] = False
            meta["randomized"] = 0
            meta["nohash"] = False
            meta["base_torrent_created"] = False
            meta["we_checked_them_all"] = False
            meta["rehash"] = False
            meta["emby"] = False
            meta["emby_debug"] = False
            meta["emby_cat"] = None
            meta["no_ids"] = False
            meta["search_requests"] = False
            meta["site_check"] = False
            meta["image_list"] = []
            meta["image_sizes"] = {}
            meta["tonemapped"] = False
            meta["frame_overlay"] = False
            meta["title"] = scenario.mediainfo.title
            meta["tmdb_id"] = scenario.tmdb_id
            meta["imdb_id"] = scenario.imdb_id
            meta["tvdb_id"] = scenario.tvdb_id
            meta["mal_id"] = 0
            meta["tvmaze_id"] = 0
            meta["uuid"] = meta.get("uuid") or os.path.basename(meta["path"])

            file_list = meta.get("filelist", [])
            if not file_list:
                if scenario.is_disc:
                    bdmv_file = Path(meta["path"]) / "BDMV" / "STREAM" / "00000.m2ts"
                    file_list = [str(bdmv_file)]
                else:
                    file_list = [meta["path"]]
            meta["filelist"] = file_list
            meta["video"] = file_list[0]
            meta["filename"] = Path(meta["path"]).stem
            meta["bdinfo"] = {
                "title": scenario.mediainfo.title,
                "video": [{"codec": "AVC", "hdr_dv": "", "fps": "23.976"}],
                "path": str(Path(meta["path"]).parent),
                "files": [{"file": Path(file_list[0]).name, "length": "01:58:34"}],
            }

            def fake_parse(_path: str, output: str = "STRING", full: bool = False):
                _ = full
                if output == "STRING":
                    return _mediainfo_text(scenario.mediainfo)
                return json.dumps(_mediainfo_json(scenario.mediainfo))

            with mock.patch("src.exportmi.MediaInfo.parse", side_effect=fake_parse), mock.patch("src.exportmi.setup_mediainfo_library", return_value=None):
                meta["mediainfo"] = await exportmi.exportInfo(
                    video=file_list[0],
                    isdir=scenario.is_disc,
                    folder_id=meta["uuid"],
                    base_dir=meta["base_dir"],
                    is_dvd=False,
                    debug=False,
                )
            return meta

        async def fake_get_name(_meta: dict[str, Any]):
            name = scenario.mediainfo.release_name().replace(".", " ")
            return name, name, name.replace(" ", "."), []

        async def fake_get_confirmation(_meta: dict[str, Any]) -> bool:
            return True

        async def fake_validate_tracker_logins(_meta: dict[str, Any], _trackers: Optional[list[str]] = None) -> None:
            return None

        async def fake_screenshots(*_args, **_kwargs) -> None:
            return None

        async def fake_upload_screens(
            _meta: dict[str, Any], _screens: int, _img_host_num: int, _i: int, _total: int, _custom: list[str], return_dict: dict[str, Any], **_kwargs
        ) -> None:
            images = [
                {
                    "img_url": "https://imgbb.com/fake1.png",
                    "raw_url": "https://imgbb.com/raw1.png",
                    "web_url": "https://imgbb.com/view1",
                },
                {
                    "img_url": "https://imgbb.com/fake2.png",
                    "raw_url": "https://imgbb.com/raw2.png",
                    "web_url": "https://imgbb.com/view2",
                },
            ]
            _meta["image_list"] = images
            return_dict.update({"image_list": images})

        async def fake_gen_desc(meta: dict[str, Any], *_args, **_kwargs) -> dict[str, Any]:
            meta["description"] = "Fake description"
            return meta

        async def fake_create_torrent(meta: dict[str, Any], _path: Path, name: str, *_args, **_kwargs) -> str:
            torrent_path = Path(meta["base_dir"]) / "tmp" / meta["uuid"] / f"{name}.torrent"
            await asyncio.to_thread(torrent_path.write_bytes, b"fake torrent")
            return str(torrent_path)

        async def fake_process_trackers(meta: dict[str, Any], *_args, **_kwargs) -> None:
            meta["tracker_status"] = {tracker: {"torrent_id": 123, "status_message": "Uploaded"} for tracker in meta.get("trackers", [])}
            captured_meta.append(meta)

        async def fake_process_cross_seeds(_meta: dict[str, Any]) -> None:
            return None

        async def fake_find_existing_torrent(_meta: dict[str, Any]):
            return None

        def fake_parse(args: list[str], meta: dict[str, Any]):
            meta = dict(meta)
            meta.update(
                {
                    "path": args[-1],
                    "screens": 3,
                    "imghost": "imgbb",
                    "trackers": [scenario.tracker],
                    "mkbrr": True,
                    "unattended": True,
                    "debug": False,
                }
            )
            return meta, None, None

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            if scenario.is_disc:
                movie_dir = temp_path / scenario.mediainfo.release_name()
                (movie_dir / "BDMV" / "STREAM").mkdir(parents=True, exist_ok=True)
                video_path = movie_dir / "BDMV" / "STREAM" / "00000.m2ts"
            else:
                movie_dir = temp_path
                video_path = movie_dir / f"{scenario.mediainfo.release_name()}.mkv"
            await asyncio.to_thread(video_path.write_bytes, b"fake video")

            argv = ["upload.py", str(movie_dir if scenario.is_disc else video_path)]
            try:
                previous_cwd = os.getcwd()
            except FileNotFoundError:
                previous_cwd = None
            os.chdir(upload.base_dir)
            try:
                with ExitStack() as stack:
                    stack.enter_context(mock.patch.object(upload, "update_notification", side_effect=fake_update_notification))
                    stack.enter_context(mock.patch.object(upload, "get_mkbrr_path", side_effect=fake_get_mkbrr_path))
                    stack.enter_context(mock.patch.object(upload.QueueManager, "handle_queue", side_effect=fake_handle_queue))
                    stack.enter_context(mock.patch.object(upload.Prep, "gather_prep", fake_gather_prep))
                    stack.enter_context(mock.patch.object(upload.name_manager, "get_name", side_effect=fake_get_name))
                    stack.enter_context(mock.patch.object(upload.UploadHelper, "get_confirmation", side_effect=fake_get_confirmation))
                    stack.enter_context(mock.patch.object(upload, "validate_tracker_logins", side_effect=fake_validate_tracker_logins))
                    stack.enter_context(mock.patch.object(upload, "TrackerStatusManager", FakeTrackerStatusManager))
                    stack.enter_context(mock.patch.object(upload.takescreens_manager, "screenshots", side_effect=fake_screenshots))
                    stack.enter_context(mock.patch.object(upload.takescreens_manager, "disc_screenshots", side_effect=fake_screenshots))
                    stack.enter_context(mock.patch.object(upload.takescreens_manager, "dvd_screenshots", side_effect=fake_screenshots))
                    stack.enter_context(mock.patch.object(upload.uploadscreens_manager, "upload_screens", side_effect=fake_upload_screens))
                    stack.enter_context(mock.patch.object(upload, "gen_desc", side_effect=fake_gen_desc))
                    stack.enter_context(mock.patch.object(upload.TorrentCreator, "create_torrent", side_effect=fake_create_torrent))
                    stack.enter_context(mock.patch.object(upload.TorrentCreator, "create_base_from_existing_torrent", side_effect=fake_create_torrent))
                    stack.enter_context(mock.patch.object(upload, "process_trackers", side_effect=fake_process_trackers))
                    stack.enter_context(mock.patch.object(upload, "process_cross_seeds", side_effect=fake_process_cross_seeds))
                    stack.enter_context(mock.patch.object(upload.client, "find_existing_torrent", side_effect=fake_find_existing_torrent))
                    stack.enter_context(mock.patch.object(upload.parser, "parse", side_effect=fake_parse))
                    stack.enter_context(mock.patch.object(upload, "tracker_class_map", tracker_map))
                    stack.enter_context(mock.patch.object(sys, "argv", argv))
                    await upload.do_the_thing(upload.base_dir)
            finally:
                if previous_cwd is None:
                    os.chdir(upload.base_dir)
                else:
                    os.chdir(previous_cwd)

            self.assertTrue(captured_meta)
            uploaded_meta = captured_meta[-1]
            self.assertEqual(uploaded_meta.get("category"), scenario.category)
            self.assertEqual(uploaded_meta.get("name"), scenario.mediainfo.release_name().replace(".", " "))
            self.assertIn(scenario.tracker, uploaded_meta.get("trackers", []))
            torrent_path = Path(uploaded_meta["base_dir"]) / "tmp" / uploaded_meta["uuid"] / "BASE.torrent"
            self.assertTrue(torrent_path.exists())

    async def test_remux_movie_flow(self) -> None:
        media = MediaInfoSpec(
            title="Fable Farm",
            year=1954,
            source="BluRay.REMUX",
            resolution="1080p",
            video_codec="AVC",
            bit_depth=8,
            frame_rate="23.976",
            duration="1 h 21 min",
            file_size_gib=14.8,
            audio_tracks=[
                AudioTrack(language="English", codec="FLAC", channels="2", bitrate_kbps=1400, title="Stereo", default=True),
                AudioTrack(language="German", codec="AC-3", channels="2", bitrate_kbps=384, title="Dub"),
            ],
            subtitle_tracks=[
                SubtitleTrack(language="English", codec="UTF-8", title="Full"),
                SubtitleTrack(language="German", codec="UTF-8", title="Full"),
            ],
            tags=["AVC", "FLAC", "2.0"],
            group="fakegrp",
        )
        scenario = Scenario(
            category="MOVIE",
            tracker="PTP",
            is_disc=False,
            tmdb_id=9009463,
            imdb_id=990248,
            tvdb_id=0,
            mediainfo=media,
        )
        await self._run_upload_flow(scenario)

    async def test_webdl_hybrid_movie_flow(self) -> None:
        media = MediaInfoSpec(
            title="Sawblade Arc",
            year=2025,
            source="WEB-DL",
            resolution="2160p",
            video_codec="HEVC",
            bit_depth=10,
            frame_rate="23.976",
            duration="1 h 46 min",
            file_size_gib=18.6,
            audio_tracks=[
                AudioTrack(language="English", codec="TrueHD", channels="7.1", bitrate_kbps=5400, title="Atmos", default=True),
                AudioTrack(language="English", codec="E-AC-3", channels="5.1", bitrate_kbps=768, title="Fallback"),
                AudioTrack(language="German", codec="E-AC-3", channels="5.1", bitrate_kbps=640, title="Dub"),
            ],
            subtitle_tracks=[
                SubtitleTrack(language="English", codec="UTF-8", title="Full"),
                SubtitleTrack(language="German", codec="UTF-8", title="Full"),
            ],
            tags=["REPACK", "MA", "DV", "HDR10P"],
            group="fakegrp",
            dual_audio=True,
        )
        scenario = Scenario(
            category="MOVIE",
            tracker="HDB",
            is_disc=False,
            tmdb_id=9014509,
            imdb_id=9990012,
            tvdb_id=0,
            mediainfo=media,
        )
        await self._run_upload_flow(scenario)

    async def test_bluray_tv_series_flow(self) -> None:
        media = MediaInfoSpec(
            title="Ozone Drift",
            year=2012,
            source="BluRay.REMUX",
            resolution="1080p",
            video_codec="AVC",
            bit_depth=8,
            frame_rate="23.976",
            duration="23 min 16 s",
            file_size_gib=4.7,
            audio_tracks=[
                AudioTrack(language="Japanese", codec="FLAC", channels="2", bitrate_kbps=1500, title="Stereo", default=True),
                AudioTrack(language="English", codec="AAC", channels="2", bitrate_kbps=192, title="Dub"),
            ],
            subtitle_tracks=[
                SubtitleTrack(language="English", codec="ASS", title="Full"),
                SubtitleTrack(language="German", codec="UTF-8", title="Full"),
            ],
            tags=["AVC", "FLAC", "2.0"],
            group="fakegrp",
            season=1,
        )
        scenario = Scenario(
            category="TV",
            tracker="BLU",
            is_disc=True,
            tmdb_id=9042941,
            imdb_id=9991001,
            tvdb_id=802581,
            mediainfo=media,
        )
        await self._run_upload_flow(scenario)

    async def test_bluray_encode_movie_flow(self) -> None:
        media = MediaInfoSpec(
            title="Everlight Gate",
            year=2011,
            source="BluRay",
            resolution="1080p",
            video_codec="HEVC",
            bit_depth=10,
            frame_rate="23.976",
            duration="1 h 32 min",
            file_size_gib=8.4,
            audio_tracks=[
                AudioTrack(language="English", codec="E-AC-3", channels="5.1", bitrate_kbps=640, title="Main", default=True),
                AudioTrack(language="French", codec="AAC", channels="2", bitrate_kbps=192, title="Dub"),
            ],
            subtitle_tracks=[
                SubtitleTrack(language="English", codec="UTF-8", title="Full"),
                SubtitleTrack(language="French", codec="UTF-8", title="Full"),
            ],
            tags=["HEVC", "E-AC-3", "5.1"],
            group="fakegrp",
        )
        scenario = Scenario(
            category="MOVIE",
            tracker="HDB",
            is_disc=False,
            tmdb_id=9005123,
            imdb_id=9992103,
            tvdb_id=0,
            mediainfo=media,
        )
        await self._run_upload_flow(scenario)


if __name__ == "__main__":
    unittest.main()
