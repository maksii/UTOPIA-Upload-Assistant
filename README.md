[![Docker Build](https://github.com/maksii/UTOPIA-Upload-Assistant/actions/workflows/docker-image.yml/badge.svg?branch=main)](https://github.com/maksii/UTOPIA-Upload-Assistant/actions/workflows/docker-image.yml)
[![Unit Tests](https://github.com/maksii/UTOPIA-Upload-Assistant/actions/workflows/test-unit.yml/badge.svg?branch=main)](https://github.com/maksii/UTOPIA-Upload-Assistant/actions/workflows/test-unit.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/maksii/utopia-upload-assistant?logo=docker&label=Docker%20Hub)](https://hub.docker.com/r/maksii/utopia-upload-assistant)
[![Python](https://img.shields.io/badge/python-3.14-blue)](https://www.python.org/downloads/)

# Upload Assistant

A simple tool to take the work out of uploading.

This project is a fork of the original work of L4G https://github.com/L4GSP1KE/Upload-Assistant
Immense thanks to him for establishing this project. Without his (and supporters) time and effort, this fork would not be a thing.
Many thanks to all who have contributed.

## About This Fork

This fork is based on [Audionut Upload Assistant](https://github.com/Audionut/Upload-Assistant). Big thanks to Audionut and the community—to everyone who contributed, used Upload Assistant, and shared it for the benefit of others.

## What It Can Do:
  - Generates and Parses MediaInfo/BDInfo.
  - Generates and Uploads screenshots. HDR tonemapping if config.
  - Uses srrdb to fix scene names used at sites.
  - Can grab descriptions from PTP/BLU/Aither/LST/OE/BHD (with config option automatically on filename match, or using arg).
  - Can strip and use existing screenshots from descriptions to skip screenshot generation and uploading.
  - Obtains TMDb/IMDb/MAL/TVDB/TVMAZE identifiers.
  - Converts absolute to season episode numbering for Anime. Non-Anime support with TVDB credentials
  - Generates custom .torrents without useless top level folders/nfos.
  - Can re-use existing torrents instead of hashing new.
  - Can automagically search qBitTorrent version 5+ clients for matching existing torrent.
  - Includes support for [qui](https://github.com/autobrr/qui)
  - Generates proper name for your upload using Mediainfo/BDInfo and TMDb/IMDb conforming to site rules.
  - Checks for existing releases already on site.
  - Adds to your client with fast resume, seeding instantly (rtorrent/qbittorrent/deluge/watch folder).
  - ALL WITH MINIMAL INPUT!
  - Currently works with .mkv/.mp4/Blu-ray/DVD/HD-DVDs.

## Supported Sites:

|Name|Acronym|Name|Acronym|
|-|:-:|-|:-:|
|Aither|AITHER|Alpharatio|AR|
|Amigos-Share|ASC|Anthelion|ANT|
|AsianCinema|ACM|Aura4K|A4K|
|AvistaZ|AZ|Beyond-HD|BHD|
|BitHDTV|BHDTV|Blutopia|BLU|
|BrasilJapão-Share|BJS|BrasilTracker|BT|
|CapybaraBR|CBR|CinemaZ|CZ|
|Cinematik|TIK|DarkPeers|DP|
|DigitalCore|DC|Emuwarez|EMUW|
|FearNoPeer|FNP|FileList|FL|
|Friki|FRIKI|FunFile|FF|
|GreatPosterWall|GPW|hawke-uno|HUNO|
|HDBits|HDB|HD-Space|HDS|
|HD-Torrents|HDT|HomieHelpDesk|HHD|
|ImmortalSeed|IS|InfinityHD|IHD|
|ItaTorrents|ITT|LastDigitalUnderground|LDU|
|Lat-Team|LT|Locadora|LCD|
|LST|LST|Luminarr|LUME|
|MoreThanTV|MTV|Nebulance|NBL|
|OldToonsWorld|OTW|OnlyEncodes+|OE|
|PassThePopcorn|PTP|PolishTorrent|PTT|
|Portugas|PT|PrivateHD|PHD|
|PTerClub|PTER|PTSKIT|PTS|
|Racing4Everyone|R4E|Rastastugan|RAS|
|ReelFLiX|RF|RetroFlix|RTF|
|Samaritano|SAM|seedpool|SP|
|ShareIsland|SHRI|SkipTheCommerials|STC|
|SpeedApp|SPD|Swarmazon|SN|
|The Leach Zone|TLZ|TheOldSchool|TOS|
|ToTheGlory|TTG|TorrentHR|THR|
|Torrenteros|TTR|TorrentLeech|TL|
|TVChaosUK|TVC|ULCX|ULCX|
|UTOPIA|UTP|YOiNKED|YOINK|
|YUSCENE|YUS|||

## **Setup:**
   - **REQUIRES PYTHON 3.14 AND PIP3**
   - Also needs MediaInfo and ffmpeg installed on your system
      - On Windows systems, ffmpeg must be added to PATH (https://windowsloop.com/install-ffmpeg-windows-10/)
      - On linux systems, get it from your favorite package manager
      - If you have issues with ffmpeg, such as `max workers` errors, see this [wiki](https://github.com/maksii/UTOPIA-Upload-Assistant/wiki/ffmpeg---max-workers-issues)
   - Get the source:
      - Clone the repo to your system `git clone https://github.com/maksii/UTOPIA-Upload-Assistant.git`
      - Fetch all of the release tags `git fetch --all --tags`
      - Check out the specifc release: see [releases](https://github.com/maksii/UTOPIA-Upload-Assistant/releases)
      - `git checkout tags/tagname` where `tagname` is the release name, eg `v5.0.0`
      - or download a zip of the source from the releases page and create/overwrite a local copy.
   - Install necessary python modules `pip3 install --user -U -r requirements.txt`
      - `sudo apt install pip` if needed
  - If you receive an error about externally managed environment, or otherwise wish to keep UA python separate:
      - Install virtual python environment `python3 -m venv venv`
      - Activate the virtual environment `source venv/bin/activate`
      - Then install the requirements `pip install -r requirements.txt`
   - From the installation directory, run `python3 config-generator.py`
   - OR
   - Copy `data/example-config.py` to `data/config.py`, leaving `data/example-config.py` intact.
   - NOTE: New users who use the webui will have the config file generated automatically.
   - Edit `config.py` to use your information (more detailed information in example config options: [docs/example-config.md](docs/example-config.md))
      - tmdb_api key can be obtained from https://www.themoviedb.org/settings/api
      - image host api keys can be obtained from their respective sites

   **Additional Resources are found in the [wiki](https://github.com/maksii/UTOPIA-Upload-Assistant/wiki)**

   Feel free to contact me if you need help, I'm not that hard to find.

## **Updating:**
  - To update first navigate into the Upload-Assistant directory: `cd Upload-Assistant`
  - `git fetch --all --tags`
  - `git checkout tags/tagname`
  - Or download a fresh zip from the releases page and overwrite existing files
  - Run `python3 -m pip install --user -U -r requirements.txt` to ensure dependencies are up to date
  - Run `python3 config-generator.py` and select to grab new UA config options.

## **CLI Usage:**

  `python3 upload.py "/path/to/content" --args`

  Args are OPTIONAL and ALWAYS follow path, for a list of acceptable args, pass `--help`.
  Path works best in quotes.
  - CLI arguments: [docs/cli-args.md](docs/cli-args.md)

## **Docker Usage:**

  ```bash
  docker pull maksii/utopia-upload-assistant:latest
  ```

  Visit our wonderful [docker usage](docs/docker-wiki-full.md)

  Also see this excellent video put together by a community member https://videos.badkitty.zone/ua

  Web UI setup (Docker GUI / Unraid): [docs/docker-gui-wiki-full.md](docs/docker-gui-wiki-full.md)
  Web UI docs: [docs/web-ui.md](docs/web-ui.md)

## **Attributions:**

Built with updated BDInfoCLI from https://github.com/rokibhasansagar/BDInfoCLI-ng

<p>
  <a href="https://github.com/autobrr/mkbrr"><img src="https://github.com/autobrr/mkbrr/blob/main/.github/assets/mkbrr-dark.png?raw=true" alt="mkbrr" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://github.com/autobrr/qui"><img src="https://github.com/autobrr/qui/blob/develop/documentation/static/img/qui.png?raw=true" alt="qui" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://ffmpeg.org/"><img src="https://i.postimg.cc/xdj3BS7S/FFmpeg-Logo-new-svg.png" alt="FFmpeg" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://mediaarea.net/en/MediaInfo"><img src="https://i.postimg.cc/vTkjXmHh/Media-Info-Logo-svg.png" alt="Mediainfo" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://www.themoviedb.org/"><img src="https://i.postimg.cc/1tpXHx3k/blue-square-2-d537fb228cf3ded904ef09b136fe3fec72548ebc1fea3fbbd1ad9e36364db38b.png" alt="TMDb" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://www.imdb.com/"><img src="https://i.postimg.cc/CLVmvwr1/IMDb-Logo-Rectangle-Gold-CB443386186.png" alt="IMDb" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://thetvdb.com/"><img src="https://i.postimg.cc/Hs1KKqsS/logo1.png" alt="TheTVDB" height="40px;"></a>&nbsp;&nbsp;
  <a href="https://www.tvmaze.com/"><img src="https://i.postimg.cc/2jdRzkJp/tvm-header-logo.png" alt="TVmaze" height="40px"></a>
</p>
