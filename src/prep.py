# -*- coding: utf-8 -*-
from src.image_upload_providers.image_uploader import ImageUploader
from src.args import Args
from src.console import console

try:
    import string
    import sys
    import traceback
    from src.discparse import DiscParse
    import multiprocessing
    import os
    from os.path import basename
    import re
    from str2bool import str2bool
    import asyncio
    from guessit import guessit
    import ntpath
    from pathlib import Path
    import urllib
    import urllib.parse
    import ffmpeg
    import random
    import json
    import glob
    import requests
    import pyimgbox
    from pymediainfo import MediaInfo
    import tmdbsimple as tmdb
    from datetime import datetime, date
    from difflib import SequenceMatcher
    from torf import Torrent
    import time
    import anitopy
    from imdb import Cinemagoer
    import subprocess
    import itertools
    from rich.prompt import Prompt
    from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
    from rich.traceback import install, Traceback
    import platform
    from requests.exceptions import HTTPError
except ModuleNotFoundError:
    console.print(traceback.print_exc())
    console.print('[bold red]Missing Module Found. Please reinstall required dependancies.')
    console.print('[yellow]pip3 install --user -U -r requirements.txt')
    exit()
except KeyboardInterrupt:
    exit()
install ()

class Prep():
    """
    Prepare for upload:
        Mediainfo/BDInfo
        Screenshots
        Database Identifiers (TMDB/IMDB/MAL/etc)
        Create Name
    """
    def __init__(self, screens, img_host, config):
        self.screens = screens
        self.config = config
        self.img_host = img_host.lower()
        tmdb.API_KEY = config['DEFAULT']['tmdb_api']


    async def gather_prep(self, meta, mode):
        meta['mode'] = mode
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        meta['isdir'] = os.path.isdir(meta['path'])
        base_dir = meta['base_dir']

        if meta.get('uuid', None) == None:
            folder_id = os.path.basename(meta['path'])
            meta['uuid'] = folder_id 
        if not os.path.exists(f"{base_dir}/tmp/{meta['uuid']}"):
            Path(f"{base_dir}/tmp/{meta['uuid']}").mkdir(parents=True, exist_ok=True)
        
        if meta['debug']:
            console.print(f"[cyan]ID: {meta['uuid']}")

        
        meta['is_disc'], videoloc, bdinfo, meta['discs'] = await self.get_disc(meta)
        
        # If BD:
        if meta['is_disc'] == "BDMV":
            video, meta['scene'], meta['imdb'] = self.is_scene(meta['path'], meta.get('imdb', None))
            meta['filelist'] = []
            try:
                guess_name = bdinfo['title'].replace('-',' ')
                filename = guessit(re.sub(r"[^0-9a-zA-Z\[\]]+", " ", guess_name), {"excludes" : ["country", "language"]})['title']
                untouched_filename = bdinfo['title']
                try:
                    meta['search_year'] = guessit(bdinfo['title'])['year']
                except Exception:
                    meta['search_year'] = ""
            except Exception:
                guess_name = bdinfo['label'].replace('-',' ')
                filename = guessit(re.sub(r"[^0-9a-zA-Z\[\]]+", " ", guess_name), {"excludes" : ["country", "language"]})['title']
                untouched_filename = bdinfo['label']
                try:
                    meta['search_year'] = guessit(bdinfo['label'])['year']
                except Exception:
                    meta['search_year'] = ""

            if meta.get('resolution', None) == None:
                meta['resolution'] = self.mi_resolution(bdinfo['video'][0]['res'], guessit(video), width="OTHER", scan="p", height="OTHER", actual_height=0)
            # if meta.get('sd', None) == None:
            meta['sd'] = self.is_sd(meta['resolution'])

            mi = None
            mi_dump = None
        #IF DVD
        elif meta['is_disc'] == "DVD":
            video, meta['scene'], meta['imdb'] = self.is_scene(meta['path'], meta.get('imdb', None))
            meta['filelist'] = []
            guess_name = meta['discs'][0]['path'].replace('-',' ')
            # filename = guessit(re.sub("[^0-9a-zA-Z]+", " ", guess_name))['title']
            filename = guessit(guess_name, {"excludes" : ["country", "language"]})['title']
            untouched_filename = os.path.basename(os.path.dirname(meta['discs'][0]['path']))
            try:
                meta['search_year'] = guessit(meta['discs'][0]['path'])['year']
            except Exception:
                meta['search_year'] = ""
            if meta.get('edit', False) == False:
                mi = self.exportInfo(f"{meta['discs'][0]['path']}/VTS_{meta['discs'][0]['main_set'][0][:2]}_1.VOB", False, meta['uuid'], meta['base_dir'], export_text=False)
                meta['mediainfo'] = mi
            else:
                mi = meta['mediainfo']
            
            #NTSC/PAL
            meta['dvd_size'] = await self.get_dvd_size(meta['discs'])
            meta['resolution'] = self.get_resolution(guessit(video), meta['uuid'], base_dir)
            meta['sd'] = self.is_sd(meta['resolution'])
        elif meta['is_disc'] == "HDDVD":
            video, meta['scene'], meta['imdb'] = self.is_scene(meta['path'], meta.get('imdb', None))
            meta['filelist'] = []
            guess_name = meta['discs'][0]['path'].replace('-','')
            filename = guessit(guess_name, {"excludes" : ["country", "language"]})['title']
            untouched_filename = os.path.basename(meta['discs'][0]['path'])
            videopath = meta['discs'][0]['largest_evo']
            try:
                meta['search_year'] = guessit(meta['discs'][0]['path'])['year']
            except Exception:
                meta['search_year'] = ""
            if meta.get('edit', False) == False:
                mi = self.exportInfo(meta['discs'][0]['largest_evo'], False, meta['uuid'], meta['base_dir'], export_text=False)
                meta['mediainfo'] = mi
            else:
                mi = meta['mediainfo']
            meta['resolution'] = self.get_resolution(guessit(video), meta['uuid'], base_dir)
            meta['sd'] = self.is_sd(meta['resolution'])
        #If NOT BD/DVD/HDDVD
        else:
            videopath, meta['filelist'] = self.get_video(videoloc, meta.get('mode', 'discord')) 
            video, meta['scene'], meta['imdb'] = self.is_scene(videopath, meta.get('imdb', None))
            guess_name = ntpath.basename(video).replace('-',' ')
            filename = guessit(re.sub(r"[^0-9a-zA-Z\[\]]+", " ", guess_name), {"excludes" : ["country", "language"]}).get("title", guessit(re.sub(r"[^0-9a-zA-Z]+", " ", guess_name), {"excludes" : ["country", "language"]})["title"])
            untouched_filename = os.path.basename(video)
            try:
                meta['search_year'] = guessit(video)['year']
            except Exception:
                meta['search_year'] = ""
            
            if meta.get('edit', False) == False:
                mi = self.exportInfo(videopath, meta['isdir'], meta['uuid'], base_dir, export_text=True)
                meta['mediainfo'] = mi
            else:
                mi = meta['mediainfo']

            if meta.get('resolution', None) == None:
                meta['resolution'] = self.get_resolution(guessit(video), meta['uuid'], base_dir)
            # if meta.get('sd', None) == None:
            meta['sd'] = self.is_sd(meta['resolution'])

        if " AKA " in filename.replace('.',' '):
            filename = filename.split('AKA')[0]
        meta['filename'] = filename

        meta['bdinfo'] = bdinfo
        
        # Take Screenshots
        if meta['is_disc'] == "BDMV":
            if meta.get('edit', False) == False:
                if meta.get('vapoursynth', False) == True:
                    use_vs = True
                else:
                    use_vs = False
                try:
                    ds = multiprocessing.Process(target=self.disc_screenshots, args=(filename, bdinfo, meta['uuid'], base_dir, use_vs, meta.get('image_list', []), meta.get('ffdebug', False), None))
                    ds.start()
                    while ds.is_alive() == True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    ds.terminate() 
        elif meta['is_disc'] == "DVD":
            if meta.get('edit', False) == False:
                try:
                    ds = multiprocessing.Process(target=self.dvd_screenshots, args=(meta, 0, None))
                    ds.start()
                    while ds.is_alive() == True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    ds.terminate()
        else:
            if meta.get('edit', False) == False:
                try:
                    s = multiprocessing.Process(target=self.screenshots, args=(videopath, filename, meta['uuid'], base_dir, meta))
                    s.start()
                    while s.is_alive() == True:
                        await asyncio.sleep(3)
                except KeyboardInterrupt:
                    s.terminate()
        meta['tmdb'] = meta.get('tmdb_manual', None)
        if meta.get('type', None) == None:
            meta['type'] = self.get_type(video, meta['scene'], meta['is_disc'])
        if meta.get('category', None) == None:
            meta['category'] = self.get_cat(video)
        else:
            meta['category'] = meta['category'].upper()
        if meta.get('tmdb', None) == None and meta.get('imdb', None) == None:
            meta['category'], meta['tmdb'], meta['imdb'] = self.get_tmdb_imdb_from_mediainfo(mi, meta['category'], meta['is_disc'], meta['tmdb'], meta['imdb'])      
        if meta.get('tmdb', None) == None and meta.get('imdb', None) == None:
            meta = await self.get_tmdb_id(filename, meta['search_year'], meta, meta['category'], untouched_filename)
        elif meta.get('imdb', None) != None and meta.get('tmdb_manual', None) == None:
            meta['imdb_id'] = str(meta['imdb']).replace('tt', '')
            meta = await self.get_tmdb_from_imdb(meta, filename)
        else:
            meta['tmdb_manual'] = meta.get('tmdb', None)

        # Check for TMDb not found
        uuid = meta.get('uuid', '')
        if meta.get('unattended') and (meta.get('tmdb') is None or int(meta['tmdb']) == 0):
            meta['tmdb_not_found'] = True
            console.print(f"[red]Unable to find TMDb match for {Path(uuid).stem}")
            return meta
        
        # If no tmdb, use imdb for meta
        if int(meta['tmdb']) == 0:
            meta = await self.imdb_other_meta(meta)
        else:
            meta = await self.tmdb_other_meta(meta)
        # Search tvmaze
        meta['tvmaze_id'], meta['imdb_id'], meta['tvdb_id'] = await self.search_tvmaze(filename, meta['search_year'], meta.get('imdb_id','0'), meta.get('tvdb_id', 0))
        # If no imdb, search for it
        if meta.get('imdb_id', None) == None:
            meta['imdb_id'] = await self.search_imdb(filename, meta['search_year'])
        if meta.get('imdb_info', None) == None and int(meta['imdb_id']) != 0:
            meta['imdb_info'] = await self.get_imdb_info(meta['imdb_id'], meta)
        if meta.get('tag', None) == None:
            meta['tag'] = self.get_tag(video, meta)
        else:
            if not meta['tag'].startswith('-') and meta['tag'] != "":
                meta['tag'] = f"-{meta['tag']}"
        meta = await self.get_season_episode(video, meta)
        meta = await self.tag_override(meta)

        meta['video'] = video
        meta['audio'], meta['channels'], meta['has_commentary'] = self.get_audio_v2(mi, meta, bdinfo)
        if meta['tag'][1:].startswith(meta['channels']):
            meta['tag'] = meta['tag'].replace(f"-{meta['channels']}", '')
        if meta.get('no_tag', False):
            meta['tag'] = ""
        meta['3D'] = self.is_3d(mi, bdinfo)
        meta['source'], meta['type'] = self.get_source(meta['type'], video, meta['path'], meta['is_disc'], meta)
        #if meta.get('service', None) in (None, ''):
        meta['service'], meta['service_longname'] = self.get_service(video, meta, meta.get('tag', ''), meta['audio'], meta['filename'])
        meta['uhd'] = self.get_uhd(meta['type'], guessit(meta['path']), meta['resolution'], meta['path'])
        meta['hdr'] = self.get_hdr(mi, bdinfo)
        meta['distributor'] = self.get_distributor(meta, meta['distributor'])
        if meta.get('is_disc', None) == "BDMV": #Blu-ray Specific
            meta['region'] = self.get_region(meta, bdinfo, meta.get('region', None))
            meta['video_codec'] = self.get_video_codec(bdinfo)
        else:
            meta['video_encode'], meta['video_codec'], meta['has_encode_settings'], meta['bit_depth'] = self.get_video_encode(mi, meta['type'], bdinfo)
        
        meta['edition'], meta['repack'], meta['cut'], meta['ratio'] = self.get_edition(meta, meta['title'], meta['path'], bdinfo, meta['filelist'], meta.get('manual_edition'))
        if "REPACK" in meta.get('edition', ""):
            meta['repack'] = re.search(r"REPACK[\d]?", meta['edition'])[0]
            meta['edition'] = re.sub(r"REPACK[\d]?", "", meta['edition']).strip().replace('  ', ' ')

        #WORK ON THIS
        meta.get('stream', False)
        meta['stream'] = self.stream_optimized(meta['stream'])
        meta.get('anon', False)
        meta['anon'] = self.is_anon(meta['anon'])

        meta = await self.gen_desc(meta)
        return meta

    """
    Determine if disc and if so, get bdinfo
    """
    async def get_disc(self, meta):
        is_disc = None
        videoloc = meta['path']
        bdinfo = None
        bd_summary = None
        discs = []
        parse = DiscParse()
        for path, directories, files in os. walk(meta['path']):
            for each in directories:
                if each.upper() == "BDMV": #BDMVs
                    is_disc = "BDMV"
                    disc = {
                        'path' : f"{path}/{each}",
                        'name' : os.path.basename(path),
                        'type' : 'BDMV',
                        'summary' : "",
                        'bdinfo' : ""
                    }
                    discs.append(disc)
                elif each == "VIDEO_TS": #DVDs
                    is_disc = "DVD"
                    disc = {
                        'path' : f"{path}/{each}",
                        'name' : os.path.basename(path),
                        'type' : 'DVD',
                        'vob_mi' : '',
                        'ifo_mi' : '',
                        'main_set' : [],
                        'size' : ""
                    }
                    discs.append(disc)
                elif each == "HVDVD_TS":
                    is_disc = "HDDVD"
                    disc = {
                        'path' : f"{path}/{each}",
                        'name' : os.path.basename(path),
                        'type' : 'HDDVD',
                        'evo_mi' : '',
                        'largest_evo' : ""
                    }
                    discs.append(disc)
        if is_disc == "BDMV":
            if meta.get('edit', False) == False:
                discs, bdinfo = await parse.get_bdinfo(discs, meta['uuid'], meta['base_dir'], meta.get('discs', []))
            else:
                discs, bdinfo = await parse.get_bdinfo(meta['discs'], meta['uuid'], meta['base_dir'], meta['discs'])
        elif is_disc == "DVD":
            discs = await parse.get_dvdinfo(discs)
            export = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/MEDIAINFO.txt", 'w', newline="", encoding='utf-8')
            export.write(discs[0]['ifo_mi'])
            export.close()
        elif is_disc == "HDDVD":
            discs = await parse.get_hddvd_info(discs)
            export = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/MEDIAINFO.txt", 'w', newline="", encoding='utf-8')
            export.write(discs[0]['evo_mi'])
            export.close()
        discs = sorted(discs, key=lambda d: d['name'])
        return is_disc, videoloc, bdinfo, discs

    """
    Get video files
    """
    def get_video(self, videoloc, mode):
        filelist = []
        videoloc = os.path.normpath(os.path.abspath(videoloc))
        if os.path.isdir(videoloc):
            globlist = glob.glob1(videoloc, "*.mkv") + glob.glob1(videoloc, "*.mp4") + glob.glob1(videoloc, "*.ts")
            for file in globlist:
                if not file.lower().endswith('sample.mkv') or "!sample" in file.lower():
                    filelist.append(os.path.abspath(f"{videoloc}{os.sep}{file}"))
            try:
                video = sorted(filelist)[0]       
            except IndexError:
                console.print("[bold red]No Video files found")
                if mode == 'cli':
                    exit()
        else:
            video = videoloc
            filelist.append(videoloc)
        filelist = sorted(filelist)
        return video, filelist

    """
    Get and parse mediainfo
    """
    def exportInfo(self, video, isdir, folder_id, base_dir, export_text):
        video = os.path.normpath(video)
        try:
            if os.path.exists(f"{base_dir}/tmp/{folder_id}/MEDIAINFO.txt") == False and export_text != False:
                console.print("[bold yellow]Exporting MediaInfo...")
            #MediaInfo to text
                if isdir == False:
                    os.chdir(os.path.dirname(video))
                media_info = MediaInfo.parse(video, output="STRING", full=False, mediainfo_options={'inform_version' : '1'})
                with open(f"{base_dir}/tmp/{folder_id}/MEDIAINFO.txt", 'w', newline="", encoding='utf-8') as export:
                    export.write(media_info)
                    export.close()
                with open(f"{base_dir}/tmp/{folder_id}/MEDIAINFO_CLEANPATH.txt", 'w', newline="", encoding='utf-8') as export_cleanpath:
                    export_cleanpath.write(media_info.replace(video, os.path.basename(video)))
                    export_cleanpath.close()
                console.print("[bold green]MediaInfo Exported.")

            if os.path.exists(f"{base_dir}/tmp/{folder_id}/MediaInfo.json.txt") == False:
                #MediaInfo to JSON
                media_info = MediaInfo.parse(video, output="JSON", mediainfo_options={'inform_version' : '1'})
                export = open(f"{base_dir}/tmp/{folder_id}/MediaInfo.json", 'w', encoding='utf-8')
                export.write(media_info)
                export.close()
            with open(f"{base_dir}/tmp/{folder_id}/MediaInfo.json", 'r', encoding='utf-8') as f:
                mi = json.load(f)
        
            return mi

        except FileNotFoundError:
            console.print(f"[bold red]File not found: {video}")
            sys.exit() 

    """
    Get Resolution
    """

    def get_resolution(self, guess, folder_id, base_dir):
        with open(f'{base_dir}/tmp/{folder_id}/MediaInfo.json', 'r', encoding='utf-8') as f:
            mi = json.load(f)
            try:
                width = mi['media']['track'][1]['Width']
                height = mi['media']['track'][1]['Height']
            except:
                width = 0
                height = 0
            framerate = mi['media']['track'][1].get('FrameRate', '')
            try:
                scan = mi['media']['track'][1]['ScanType']
            except:
                scan = "Progressive"
            if scan == "Progressive":
                scan = "p"
            elif framerate == "25.000":
                scan = "p"
            else:
                scan = "i"
            width_list = [3840, 2560, 1920, 1280, 1024, 854, 720, 15360, 7680, 0]
            height_list = [2160, 1440, 1080, 720, 576, 540, 480, 8640, 4320, 0]
            width = self.closest(width_list, int(width))
            actual_height = int(height)
            height = self.closest(height_list, int(height))
            res = f"{width}x{height}{scan}"
            resolution = self.mi_resolution(res, guess, width, scan, height, actual_height)
        return resolution

    def closest(self, lst, K):
        # Get closest, but not over
        lst = sorted(lst)
        mi_input = K
        res = 0
        for each in lst:
            if mi_input > each:
                pass
            else:
                res = each
                break
        return res

    def mi_resolution(self, res, guess, width, scan, height, actual_height):
        res_map = {
            "3840x2160p" : "2160p", "2160p" : "2160p",
            "2560x1440p" : "1440p", "1440p" : "1440p",
            "1920x1080p" : "1080p", "1080p" : "1080p",
            "1920x1080i" : "1080i", "1080i" : "1080i", 
            "1280x720p" : "720p", "720p" : "720p",
            "1280x540p" : "720p", "1280x576p" : "720p",
            "1024x576p" : "576p", "576p" : "576p",
            "1024x576i" : "576i", "576i" : "576i",
            "854x480p" :  "480p", "480p" : "480p",
            "854x480i" : "480i", "480i" : "480i",
            "720x576p" : "576p", "576p" : "576p",
            "720x576i" : "576i", "576i" : "576i",
            "720x480p" :  "480p", "480p" : "480p",
            "720x480i" : "480i", "480i" : "480i",
            "15360x8640p" : "8640p", "8640p" : "8640p",
            "7680x4320p" : "4320p", "4320p" : "4320p",
            "OTHER" : "OTHER"}
        resolution = res_map.get(res, None)
        if actual_height == 540:
            resolution = "OTHER"
        if resolution == None:
            try:     
                resolution = guess['screen_size']
            except:
                width_map = {
                    '3840p' : '2160p',
                    '2560p' : '1550p',
                    '1920p' : '1080p',
                    '1920i' : '1080i',
                    '1280p' : '720p',
                    '1024p' : '576p',
                    '1024i' : '576i',
                    '854p' : '480p',
                    '854i' : '480i',
                    '720p' : '576p',
                    '720i' : '576i',
                    '15360p' : '4320p',
                    'OTHERp' : 'OTHER'
                }
                resolution = width_map.get(f"{width}{scan}", "OTHER")
            resolution = self.mi_resolution(resolution, guess, width, scan, height, actual_height)
        
        return resolution
    
    def is_sd(self, resolution):
        if resolution in ("480i", "480p", "576i", "576p", "540p"):
            sd = 1
        else:
            sd = 0
        return sd

    """
    Is a scene release?
    """
    def is_scene(self, video, imdb=None):
        scene = False
        base = os.path.basename(video)
        base = os.path.splitext(base)[0]
        base = urllib.parse.quote(base)
        url = f"https://api.srrdb.com/v1/search/r:{base}"
        try:
            response = requests.get(url, timeout=30)
            response = response.json()
            if int(response.get('resultsCount', 0)) != 0:
                video = f"{response['results'][0]['release']}.mkv"
                scene = True
                r = requests.get(f"https://api.srrdb.com/v1/imdb/{base}")
                r = r.json()
                if r['releases'] != [] and imdb == None:
                    imdb = r['releases'][0].get('imdb', imdb) if r['releases'][0].get('imdb') is not None else imdb
                console.print(f"[green]SRRDB: Matched to {response['results'][0]['release']}")
        except Exception:
            video = video
            scene = False
            console.print("[yellow]SRRDB: No match found, or request has timed out")
        return video, scene, imdb

    """
    Generate Screenshots
    """

    def disc_screenshots(self, filename, bdinfo, folder_id, base_dir, use_vs, image_list, ffdebug, num_screens=None):
        if num_screens == None:
            num_screens = self.screens
        if num_screens == 0 or len(image_list) >= num_screens:
            return
        #Get longest m2ts
        length = 0 
        for each in bdinfo['files']:
            int_length = sum(int(float(x)) * 60 ** i for i, x in enumerate(reversed(each['length'].split(':'))))
            if int_length > length:
                length = int_length
                for root, dirs, files in os.walk(bdinfo['path']):
                    for name in files:
                        if name.lower() == each['file'].lower():
                            file = f"{root}/{name}"
                            
        
        if "VC-1" in bdinfo['video'][0]['codec'] or bdinfo['video'][0]['hdr_dv'] != "":
            keyframe = 'nokey'
        else:
            keyframe = 'none'

        os.chdir(f"{base_dir}/tmp/{folder_id}")    
        i = len(glob.glob(f"{filename}-*.png"))        
        if i >= num_screens:
            i = num_screens
            console.print('[bold green]Reusing screenshots')
        else:
            console.print("[bold yellow]Saving Screens...")
            if use_vs == True:
                from src.vs import vs_screengn
                vs_screengn(source=file, encode=None, filter_b_frames=False, num=num_screens, dir=f"{base_dir}/tmp/{folder_id}/")
            else:
                if bool(ffdebug) == True:
                    loglevel = 'verbose'
                    debug = False
                else:
                    loglevel = 'quiet'
                    debug = True
                retake = False    
                with Progress(
                    TextColumn("[bold green]Saving Screens..."),
                    BarColumn(),
                    "[cyan]{task.completed}/{task.total}",
                    TimeRemainingColumn()
                ) as progress:
                    screen_task = progress.add_task("[green]Saving Screens...", total=num_screens)
                    ss_times = []
                    smallest_image_path = None
                    smallest_image_size = float('inf')

                    for _ in range(num_screens):
                        image_path = f"{base_dir}/tmp/{folder_id}/{filename}-{i}.png"
                        if not os.path.exists(image_path) or retake:                       
                            try:
                                ss_times = self.valid_ss_time(ss_times, num_screens, length)
                                (
                                    ffmpeg
                                    .input(file, ss=ss_times[-1], skip_frame=keyframe)
                                    .output(image_path, vframes=1, pix_fmt="rgb24")
                                    .overwrite_output()
                                    .global_args('-loglevel', loglevel)
                                    .run(quiet=debug)
                                )
                            except Exception:
                                console.print(traceback.format_exc())
                            
                            self.optimize_images(image_path)
                            if os.path.getsize(Path(image_path)) <= 75000:
                                console.print("[bold yellow]Image is incredibly small, retaking")
                                time.sleep(1)                            
                            elif os.path.getsize(Path(image_path)) <= 31000000 and self.img_host == "imgbb":
                                i += 1
                            elif os.path.getsize(Path(image_path)) <= 10000000 and self.img_host in ["imgbox", "pixhost", "ptscreens", "oeimg" ]:
                                i += 1
                            elif self.img_host in ["ptpimg", "lensdump"] and not retake:
                                i += 1
                            elif retake:
                                pass                               
                            else:
                                console.print("[red]Image too large for your image host, retaking")
                                time.sleep(1)
                        else:
                            screenshot_size = os.path.getsize(image_path)
                            if screenshot_size < smallest_image_size:
                                smallest_image_size = screenshot_size
                                smallest_image_path = image_path

                        i += 1
                        progress.advance(screen_task)
                        
                    # Remove the smallest image
                    if smallest_image_path:
                        os.remove(smallest_image_path)
        
    def dvd_screenshots(self, meta, disc_num, num_screens=None):
        if num_screens is None:
            num_screens = self.screens
        if num_screens == 0 or (len(meta.get('image_list', [])) >= num_screens and disc_num == 0):
            return
        ifo_mi = MediaInfo.parse(f"{meta['discs'][disc_num]['path']}/VTS_{meta['discs'][disc_num]['main_set'][0][:2]}_0.IFO", mediainfo_options={'inform_version': '1'})
        sar = 1
        for track in ifo_mi.tracks:
            if track.track_type == "Video":
                length = float(track.duration) / 1000
                par = float(track.pixel_aspect_ratio)
                dar = float(track.display_aspect_ratio)
                width = float(track.width)
                height = float(track.height)
        if par < 1:
            new_height = dar * height
            sar = width / new_height
            w_sar = 1
            h_sar = sar
        else:
            sar = par
            w_sar = sar
            h_sar = 1

        main_set_length = len(meta['discs'][disc_num]['main_set'])
        if main_set_length >= 3:
            main_set = meta['discs'][disc_num]['main_set'][1:-1]
        elif main_set_length == 2:
            main_set = meta['discs'][disc_num]['main_set'][1:]
        elif main_set_length == 1:
            main_set = meta['discs'][disc_num]['main_set']
        n = 0
        os.chdir(f"{meta['base_dir']}/tmp/{meta['uuid']}")
        i = 0
        existing_screenshots = glob.glob(f"{meta['base_dir']}/tmp/{meta['uuid']}/{meta['discs'][disc_num]['name']}-*.png")

        if len(existing_screenshots) >= num_screens:
            i = num_screens
            console.print('[bold green]Reusing screenshots')
        else:
            if meta.get('ffdebug', False):
                loglevel = 'verbose'
                debug = False
            looped = 0
            retake = False
            with Progress(
                TextColumn("[bold green]Saving Screens..."),
                BarColumn(),
                "[cyan]{task.completed}/{task.total}",
                TimeRemainingColumn()
            ) as progress:
                screen_task = progress.add_task("[green]Saving Screens...", total=num_screens)
                ss_times = []
                smallest_image_path = None
                smallest_image_size = float('inf')
                for i in range(num_screens):
                    if n >= len(main_set):
                        n = 0
                    if n >= num_screens:
                        n -= num_screens
                    image = f"{meta['base_dir']}/tmp/{meta['uuid']}/{meta['discs'][disc_num]['name']}-{i}.png"
                    if not os.path.exists(image) or retake:
                        try:
                            retake = False
                            loglevel = 'quiet'
                            debug = True
                            if bool(meta.get('debug', False)):
                                loglevel = 'error'
                                debug = False
                            def _is_vob_good(n, num_screens):
                                voblength = 300
                                loops = 0
                                while loops < 6:
                                    vob_mi = MediaInfo.parse(f"{meta['discs'][disc_num]['path']}/VTS_{main_set[n]}", output='JSON')
                                    vob_mi = json.loads(vob_mi)
                                    try:
                                        voblength = float(vob_mi['media']['track'][1]['Duration'])
                                        return voblength, n
                                    except Exception:
                                        try:
                                            voblength = float(vob_mi['media']['track'][2]['Duration'])
                                            return voblength, n
                                        except Exception:
                                            n += 1
                                            if n >= len(main_set):
                                                n = 0
                                            if n >= num_screens:
                                                n -= num_screens
                                            loops += 1
                                return 300, n

                            try:
                                voblength, n = _is_vob_good(n, num_screens)
                                m = i
                                min_time = 0.01 * voblength
                                base_time = max(min_time, random.randint(round(voblength / 5), round(voblength - voblength / 5)))
                                while True:
                                    img_time = max(min_time, base_time / (2 ** m) + random.uniform(0, 20))
                                    if img_time < voblength:
                                        break
                                ff = ffmpeg.input(f"{meta['discs'][disc_num]['path']}/VTS_{main_set[n]}", ss=img_time)
                                if w_sar != 1 or h_sar != 1:
                                    ff = ff.filter('scale', int(round(width * w_sar)), int(round(height * h_sar))) 
                                (
                                    ff
                                    .output(image, vframes=1, pix_fmt="rgb24")
                                    .overwrite_output()
                                    .global_args('-loglevel', loglevel)
                                    .run(quiet=debug)
                                )                           
                            except Exception:
                                console.print(traceback.format_exc())

                            self.optimize_images(image)
                            n += 1

                            try:
                                if os.path.getsize(Path(image)) <= 31000000 and self.img_host == "imgbb":
                                    i += 1
                                elif os.path.getsize(Path(image)) <= 10000000 and self.img_host in ["imgbox", 'pixhost', "ptscreens", "oeimg"]:
                                    i += 1
                                elif os.path.getsize(Path(image)) <= 75000:
                                    console.print("[yellow]Image is incredibly small (and is most likely to be a single color), retaking")
                                    retake = True
                                    time.sleep(1)
                                elif self.img_host == "ptpimg":
                                    i += 1
                                elif self.img_host == "lensdump":
                                    i += 1
                                else:
                                    console.print("[red]Image too large for your image host, retaking")
                                    retake = True
                                    time.sleep(1)
                                looped = 0
                            except Exception:
                                if looped >= 25:
                                    console.print('[red]Failed to take screenshots')
                                    exit()
                                looped += 1

                            progress.advance(screen_task)

                        except Exception:
                            pass
                    else:
                        screenshot_size = os.path.getsize(image)
                        if screenshot_size < smallest_image_size:
                            smallest_image_size = screenshot_size
                            smallest_image_path = image

                    i += 1

            # Remove the smallest image
            if smallest_image_path:
                os.remove(smallest_image_path)

    def screenshots(self, path, filename, folder_id, base_dir, meta, num_screens=None):
        if num_screens is None:
            num_screens = self.screens - len(meta.get('image_list', []))
        if num_screens == 0:
            return
        with open(f"{base_dir}/tmp/{folder_id}/MediaInfo.json", encoding='utf-8') as f:
            mi = json.load(f)
            video_track = mi['media']['track'][1]
            length = float(video_track.get('Duration', mi['media']['track'][0]['Duration']))
            width = float(video_track.get('Width'))
            height = float(video_track.get('Height'))
            par = float(video_track.get('PixelAspectRatio', 1))
            dar = float(video_track.get('DisplayAspectRatio'))

            if par == 1:
                sar = w_sar = h_sar = 1
            elif par < 1:
                new_height = dar * height
                sar = width / new_height
                w_sar = 1
                h_sar = sar
            else:
                sar = w_sar = par 
                h_sar = 1
            length = round(length)
            os.chdir(f"{base_dir}/tmp/{folder_id}")
            i = 0
            if len(glob.glob(f"{filename}-*.png")) >= num_screens:
                i = num_screens
                console.print('[bold green]Reusing screenshots')
            else:
                loglevel = 'quiet'
                debug = True
                if bool(meta.get('ffdebug', False)):
                    loglevel = 'verbose'
                    debug = False
                if meta.get('vapoursynth', False):
                    from src.vs import vs_screengn
                    vs_screengn(source=path, encode=None, filter_b_frames=False, num=num_screens, dir=f"{base_dir}/tmp/{folder_id}/")
                else:
                    retake = False
                    with Progress(
                        TextColumn("[bold green]Saving Screens..."),
                        BarColumn(),
                        "[cyan]{task.completed}/{task.total}",
                        TimeRemainingColumn()
                    ) as progress:
                        ss_times = []
                        screen_task = progress.add_task("[green]Saving Screens...", total=num_screens)
                        smallest_image_path = None
                        smallest_image_size = float('inf')
                        
                        for _ in range(num_screens):
                            image_path = os.path.abspath(f"{base_dir}/tmp/{folder_id}/{filename}-{i}.png")
                            
                            if not os.path.exists(image_path) or retake:
                                try:
                                    ss_times = self.valid_ss_time(ss_times, num_screens, length)
                                    ff = ffmpeg.input(path, ss=ss_times[-1])
                                    if w_sar != 1 or h_sar != 1:
                                        ff = ff.filter('scale', int(round(width * w_sar)), int(round(height * h_sar)))
                                    (
                                        ff
                                        .output(image_path, vframes=1, pix_fmt="rgb24")
                                        .overwrite_output()
                                        .global_args('-loglevel', loglevel)
                                        .run(quiet=debug)
                                    )
                                except Exception as e:
                                    console.print(Traceback.extract())
                                    self.optimize_images(image_path)
                                    if os.path.exists(image_path):
                                        if os.path.getsize(Path(image_path)) <= 75000 or self.is_black_image(image_path):
                                            console.print("[yellow]Image is incredibly small or black, retaking")
                                            retake = True
                                            os.remove(image_path)
                                            time.sleep(1)
                                        elif os.path.getsize(Path(image_path)) <= 31000000 and self.img_host == "imgbb" and not retake:
                                            i += 1
                                        elif os.path.getsize(Path(image_path)) <= 10000000 and self.img_host in ["imgbox", 'pixhost', "ptscreens", "oeimg"] and not retake:
                                            i += 1
                                        elif self.img_host in ["ptpimg", "lensdump"] and not retake:
                                            i += 1
                                        elif self.img_host == "freeimage.host":
                                            console.print("[bold red]Support for freeimage.host has been removed. Please remove from your config")
                                            exit()
                                        elif retake:
                                            pass
                                        else:
                                            console.print("[red]Image too large for your image host, retaking")
                                            retake = True
                                            os.remove(image_path)
                                            time.sleep(1)
                            else:
                                screenshot_size = os.path.getsize(image_path)
                                if screenshot_size < smallest_image_size:
                                    smallest_image_size = screenshot_size
                                    smallest_image_path = image_path

                            i += 1
                            progress.advance(screen_task)
                            
                        # Remove the smallest image
                        if smallest_image_path:
                            os.remove(smallest_image_path)
                            
    def is_black_image(image_path, threshold=0.98):
        try:
            command = [
                'ffmpeg', '-i', image_path, '-vf', 
                'blackdetect=d=0.1:pic_th=%f' % threshold, '-f', 'null', '-'
            ]
            result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            return 'black_start' in result.stderr
        except Exception as e:
            console.print(f"[red]Error checking black image: {e}")
            return False         
        
    def valid_ss_time(self, ss_times, num_screens, length, min_time_diff=10):
        valid_time = False
        while not valid_time:
            valid_time = True
            if ss_times:
                sst = random.randint(round(length / 5), round(length / 2))
                tolerance = length / 10 / num_screens
                for each in ss_times:
                    if abs(sst - each) <= tolerance or any(abs(sst - t) < min_time_diff for t in ss_times):
                        valid_time = False
                if valid_time:
                    ss_times.append(sst)
            else:
                ss_times.append(random.randint(round(length / 5), round(length / 2)))
        return ss_times

    def optimize_images(self, image):
        if self.config['DEFAULT'].get('optimize_images', True):
            if os.path.exists(image):
                try:
                    pyver = platform.python_version_tuple()
                    if int(pyver[0]) == 3 and int(pyver[1]) >= 7:
                        import oxipng 
                    if os.path.getsize(image) >= 31000000:
                        oxipng.optimize(image, level=6)
                    else:
                        oxipng.optimize(image, level=1)
                except:
                    pass
        return
    """
    Get type and category
    """

    def get_type(self, video, scene, is_disc):
        filename = os.path.basename(video).lower()
        if "remux" in filename:
            type = "REMUX"
        elif any(word in filename for word in [" web ", ".web.", "web-dl"]):
            type = "WEBDL"
        elif "webrip" in filename:
            type = "WEBRIP"
        # elif scene == True:
            # type = "ENCODE"
        elif "hdtv" in filename:
            type = "HDTV"
        elif is_disc != None:
            type = "DISC"
        elif "dvdrip" in filename:
            console.print("[bold red]DVDRip Detected, exiting")
            exit()
        else:
            type = "ENCODE"
        return type

    def get_cat(self, video):
        # if category is None:
        category = guessit(video.replace('1.0', ''))['type']
        if category.lower() == "movie":
            category = "MOVIE" #1
        elif category.lower() in ("tv", "episode"):
            category = "TV" #2
        else:
            category = "MOVIE"
        return category

    async def get_tmdb_from_imdb(self, meta, filename):
        if meta.get('tmdb_manual') is not None:
            meta['tmdb'] = meta['tmdb_manual']
            return meta
        imdb_id = meta['imdb']
        if str(imdb_id)[:2].lower() != "tt":
            imdb_id = f"tt{imdb_id}"
        find = tmdb.Find(id=imdb_id)
        info = find.info(external_source="imdb_id")
        if len(info['movie_results']) >= 1:
            meta['category'] = "MOVIE"
            meta['tmdb'] =  info['movie_results'][0]['id']
        elif len(info['tv_results']) >= 1:
            meta['category'] = "TV"
            meta['tmdb'] =  info['tv_results'][0]['id']
        else:
            imdb_info = await self.get_imdb_info(imdb_id.replace('tt', ''), meta)
            title = imdb_info.get("title")
            if title == None:
                title = filename
            year = imdb_info.get('year')
            if year == None:
                year = meta['search_year']
            console.print(f"[yellow]TMDb was unable to find anything with that IMDb, searching TMDb for {title}")
            meta = await self.get_tmdb_id(title, year, meta, meta['category'], imdb_info.get('original title', imdb_info.get('localized title', meta['uuid'])))
            if meta.get('tmdb') in ('None', '', None, 0, '0'):
                if meta.get('mode', 'discord') == 'cli':
                    console.print('[yellow]Unable to find a matching TMDb entry')
                    tmdb_id = console.input("Please enter tmdb id: ")
                    parser = Args(config=self.config)
                    meta['category'], meta['tmdb'] = parser.parse_tmdb_id(id=tmdb_id, category=meta.get('category'))
        await asyncio.sleep(2)
        return meta

    async def get_tmdb_id(self, filename, search_year, meta, category, untouched_filename="", attempted=0):
        search = tmdb.Search()
        try:
            if category == "MOVIE":
                search.movie(query=filename, year=search_year)
            elif category == "TV":
                search.tv(query=filename, first_air_date_year=search_year)
            if meta.get('tmdb_manual') is not None:
                meta['tmdb'] = meta['tmdb_manual']
            else:
                meta['tmdb'] = search.results[0]['id']
                meta['category'] = category 
        except IndexError:
            try:
                if category == "MOVIE":
                    search.movie(query=filename)
                elif category == "TV":
                    search.tv(query=filename)
                meta['tmdb'] = search.results[0]['id']
                meta['category'] = category
            except IndexError:
                if category == "MOVIE":
                    category = "TV"
                else:
                    category = "MOVIE"
                
                if attempted <= 1:
                    attempted += 1
                    meta = await self.get_tmdb_id(filename, search_year, meta, category, untouched_filename, attempted)
                elif attempted == 2:
                    attempted += 1
                    parsed_title = anitopy.parse(guessit(untouched_filename, {"excludes": ["country", "language"]})['title'])['anime_title']
                    meta = await self.get_tmdb_id(parsed_title, search_year, meta, meta['category'], untouched_filename, attempted)

                if meta.get('tmdb') in (None, ""):
                    console.print(f"[red]Unable to find TMDb match for {filename}")
                    if meta.get('unattended'):
                        meta['tmdb_not_found'] = True
                        return meta
                    else:
                        tmdb_id = Prompt.ask(f"Please enter tmdb id in this format: tv/12345 or movie/12345\n")
                        parser = Args(config=self.config)
                        meta['category'], meta['tmdb'] = parser.parse_tmdb_id(id=tmdb_id, category=meta.get('category'))
                        meta['tmdb_manual'] = meta['tmdb']
                        return meta

        return meta
    
    async def tmdb_other_meta(self, meta):
        
        if meta['tmdb'] == "0":
            try:
                title = guessit(meta['path'], {"excludes" : ["country", "language"]})['title'].lower()
                title = title.split('aka')[0]
                meta = await self.get_tmdb_id(guessit(title, {"excludes" : ["country", "language"]})['title'], meta['search_year'], meta)
                if meta['tmdb'] == "0":
                    meta = await self.get_tmdb_id(title, "", meta, meta['category'])
            except:
                if meta.get('mode', 'discord') == 'cli':
                    console.print("[bold red]Unable to find tmdb entry. Exiting.")
                    exit()
                else:
                    console.print("[bold red]Unable to find tmdb entry")
                    return meta
        if meta['category'] == "MOVIE":
            movie = tmdb.Movies(meta['tmdb'])
            while True:  # Keep looping until a valid response is obtained
                try:
                    response = movie.info()
                    break 
                except HTTPError as e:
                    if e.response.status_code == 404:
                        console.print("[red]The TMDb ID you entered could not be found. Please make sure the ID is correct and try again.")
                        tmdb_id = Prompt.ask(f"Please enter tmdb id in this format: tv/12345 or movie/12345\n")
                        parser = Args(config=self.config)
                        meta['category'], meta['tmdb'] = parser.parse_tmdb_id(id=tmdb_id, category=meta.get('category'))
                        meta['tmdb_manual'] = meta['tmdb']
                        movie = tmdb.Movies(meta['tmdb'])  # Update the movie object with the new TMDb ID
                    else:
                        raise
            meta['title'] = response['title']
            if response['release_date']:
                try:
                    meta['year'] = datetime.strptime(response['release_date'],'%Y-%m-%d').year
                    full_date = datetime.strptime(response['release_date'],'%Y-%m-%d')
                    meta['full_date'] = full_date.strftime('%Y-%m-%d')
                except Exception:
                    meta['full_date'] = ""
            else:
                console.print('[yellow]TMDB does not have a release date, using year from filename instead (if it exists)')
                meta['year'] = meta['search_year']
            external = movie.external_ids()
            if meta.get('imdb', None) == None:
                imdb_id = external.get('imdb_id', "0")
                if imdb_id == "" or imdb_id == None:
                    meta['imdb_id'] = '0'
                else:
                    meta['imdb_id'] = str(int(imdb_id.replace('tt', ''))).zfill(7)
            else:
                meta['imdb_id'] = str(meta['imdb']).replace('tt', '').zfill(7)
            if meta.get('tvdb_id', '0') in ['', ' ', None, 'None', '0']:
                meta['tvdb_id'] = external.get('tvdb_id', '0')
                if meta['tvdb_id'] in ["", None, " ", "None"]:
                    meta['tvdb_id'] = '0'
            try:
                videos = movie.videos()
                for each in videos.get('results', []):
                    if each.get('site', "") == 'YouTube' and each.get('type', "") == "Trailer":
                        meta['youtube'] = f"{each.get('key')}"
                        break
            except Exception:
                console.print('[yellow]Unable to grab videos from TMDb.')
            
            meta['aka'], original_language = await self.get_imdb_aka(meta['imdb_id'])
            if original_language != None:
                meta['original_language'] = original_language
            else:
                meta['original_language'] = response['original_language']

            meta['original_title'] = response.get('original_title', meta['title'])
            meta['keywords'] = self.get_keywords(movie)
            meta['genres'] = self.get_genres(response)
            meta['adult'] = response['adult']
            meta['tmdb_directors'] = self.get_directors(movie)
            if meta.get('anime', False) == False:
                meta['mal_id'], meta['aka'], meta['anime'] = self.get_anime(response, meta)
            meta['poster'] = response.get('poster_path', "")
            meta['overview'] = response['overview']
            meta['tmdb_type'] = 'Movie'
            meta['runtime'] = response.get('episode_run_time', 60)
        elif meta['category'] == "TV":
            tv = tmdb.TV(meta['tmdb'])
            response = tv.info()
            meta['title'] = response['name']
            if response['first_air_date']:
                try:
                    meta['year'] = datetime.strptime(response['first_air_date'],'%Y-%m-%d').year
                    full_date = datetime.strptime(response['first_air_date'],'%Y-%m-%d')
                    meta['full_date'] = full_date.strftime('%Y-%m-%d')
                except Exception:
                    meta['full_date'] = ""
            else:
                console.print('[yellow]TMDB does not have a release date, using year from filename instead (if it exists)')
                meta['year'] = meta['search_year']
            external = tv.external_ids()
            if meta.get('imdb', None) == None:
                imdb_id = external.get('imdb_id', "0")
                if imdb_id == "" or imdb_id == None:
                    meta['imdb_id'] = '0'
                else:
                    meta['imdb_id'] = str(int(imdb_id.replace('tt', ''))).zfill(7)
            else:
                meta['imdb_id'] = str(int(meta['imdb'].replace('tt', ''))).zfill(7)
            if meta.get('tvdb_id', '0') in ['', ' ', None, 'None', '0']:
                meta['tvdb_id'] = external.get('tvdb_id', '0')
                if meta['tvdb_id'] in ["", None, " ", "None"]:
                    meta['tvdb_id'] = '0'
            try:
                videos = tv.videos()
                for each in videos.get('results', []):
                    if each.get('site', "") == 'YouTube' and each.get('type', "") == "Trailer":
                        meta['youtube'] = f"{each.get('key')}"
                        break
            except Exception:
                console.print('[yellow]Unable to grab videos from TMDb.')

            meta['aka'], original_language = await self.get_imdb_aka(meta['imdb_id'])
            if original_language != None:
                meta['original_language'] = original_language
            else:
                meta['original_language'] = response['original_language']
            meta['original_title'] = response.get('original_name', meta['title'])
            meta['keywords'] = self.get_keywords(tv)
            meta['genres'] = self.get_genres(response)
            meta['adult'] = response['adult']
            meta['tmdb_directors'] = self.get_directors(tv)
            meta['mal_id'], meta['aka'], meta['anime'] = self.get_anime(response, meta)
            meta['poster'] = response.get('poster_path', '')
            meta['overview'] = response['overview']

            meta['tmdb_type'] = response.get('type', 'Scripted')
            runtime = response.get('episode_run_time', [60])
            if runtime == []:
                runtime = [60]
            meta['runtime'] = runtime[0]
        if meta['poster'] not in (None, ''):
            meta['poster'] = f"https://image.tmdb.org/t/p/original{meta['poster']}"

        difference = SequenceMatcher(None, meta['title'].lower(), meta['aka'][5:].lower()).ratio()
        if difference >= 0.9 or meta['aka'][5:].strip() == "" or meta['aka'][5:].strip().lower() in meta['title'].lower():
            meta['aka'] = ""
        if f"({meta['year']})" in meta['aka']:
            meta['aka'] = meta['aka'].replace(f"({meta['year']})", "").strip()

        return meta

    def get_keywords(self, tmdb_info):
        if tmdb_info is not None:
            tmdb_keywords = tmdb_info.keywords()
            if tmdb_keywords.get('keywords') is not None:
                keywords=[f"{keyword['name'].replace(',',' ')}" for keyword in tmdb_keywords.get('keywords')]
            elif tmdb_keywords.get('results') is not None:
                keywords=[f"{keyword['name'].replace(',',' ')}" for keyword in tmdb_keywords.get('results')]
            return(', '.join(keywords))
        else:
            return ''

    def get_genres(self, tmdb_info):
        if tmdb_info is not None:
            tmdb_genres = tmdb_info.get('genres', [])
            if tmdb_genres is not []:
                genres=[f"{genre['name'].replace(',',' ')}" for genre in tmdb_genres]
            return(', '.join(genres))
        else:
            return ''

    def get_directors(self, tmdb_info):
        if tmdb_info is not None:
            tmdb_credits = tmdb_info.credits()
            directors = []
            if tmdb_credits.get('cast', []) != []:
                for each in tmdb_credits['cast']:
                    if each.get('known_for_department', '') == "Directing":
                        directors.append(each.get('original_name', each.get('name')))
            return directors
        else:
            return ''

    def get_anime(self, response, meta):
        tmdb_name = meta['title']
        if meta.get('aka', "") == "":
            alt_name = ""
        else:
            alt_name = meta['aka']
        anime = False
        animation = False
        for each in response['genres']:
            if each['id'] == 16:
                animation = True
        if response['original_language'] == 'ja' and animation == True:
            romaji, mal_id, eng_title, season_year, episodes = self.get_romaji(tmdb_name, meta.get('mal', None))
            alt_name = f" AKA {romaji}"
            
            anime = True
        else:
            mal_id = 0
        if meta.get('mal_id', 0) != 0:
            mal_id = meta.get('mal_id')
        if meta.get('mal') not in ('0', 0, None):
            mal_id = meta.get('mal', 0)
        return mal_id, alt_name, anime

    def get_romaji(self, tmdb_name, mal):
        if mal == None:
            mal = 0
            tmdb_name = tmdb_name.replace('-', "").replace("The Movie", "")
            tmdb_name = ' '.join(tmdb_name.split())
            query = '''
                query ($search: String) {
                    Page (page: 1) {
                        pageInfo {
                            total
                        }
                    media (search: $search, type: ANIME, sort: SEARCH_MATCH) {
                        id
                        idMal
                        title {
                            romaji
                            english
                            native
                        }
                        seasonYear
                        episodes
                    }
                }
            }
            '''
            # Define our query variables and values that will be used in the query request
            variables = {
                'search': tmdb_name
            }
        else:
            query = '''
                query ($search: Int) {
                    Page (page: 1) {
                        pageInfo {
                            total
                        }
                    media (idMal: $search, type: ANIME, sort: SEARCH_MATCH) {
                        id
                        idMal
                        title {
                            romaji
                            english
                            native
                        }
                        seasonYear
                        episodes
                    }
                }
            }
            '''
            # Define our query variables and values that will be used in the query request
            variables = {
                'search': mal
            }

        # Make the HTTP Api request
        url = 'https://graphql.anilist.co'
        try:
            response = requests.post(url, json={'query': query, 'variables': variables})
            json = response.json()
            media = json['data']['Page']['media']
        except:
            console.print('[red]Failed to get anime specific info from anilist. Continuing without it...')
            media = []
        if media not in (None, []):
            result = {'title' : {}}
            difference = 0
            for anime in media:
                search_name = re.sub(r"[^0-9a-zA-Z\[\]]+", "", tmdb_name.lower().replace(' ', ''))
                for title in anime['title'].values():
                    if title != None:
                        title = re.sub(u'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf\u3400-\u4dbf]+ (?=[A-Za-z ]+–)', "", title.lower().replace(' ', ''), re.U)
                        diff = SequenceMatcher(None, title, search_name).ratio()
                        if diff >= difference:
                            result = anime
                            difference = diff

            romaji = result['title'].get('romaji', result['title'].get('english', ""))
            mal_id = result.get('idMal', 0)
            eng_title = result['title'].get('english', result['title'].get('romaji', ""))
            season_year = result.get('season_year', "")
            episodes = result.get('episodes', 0)
        else:
            romaji = eng_title = season_year  = ""
            episodes = mal_id = 0
        if mal_id in [None, 0]:
            mal_id = mal
        if not episodes:
            episodes = 0
        return romaji, mal_id, eng_title, season_year, episodes

    """
    Mediainfo/Bdinfo > meta
    """
    def get_audio_v2(self, mi, meta, bdinfo):
        extra = dual = ""
        has_commentary = False
        #Get formats
        if bdinfo != None: #Disks
            format_settings = ""
            format = bdinfo['audio'][0]['codec']
            commercial = format
            try:
                additional = bdinfo['audio'][0]['atmos_why_you_be_like_this']
            except:
                additional = ""
            #Channels
            chan = bdinfo['audio'][0]['channels']
        else: 
            track_num = 2
            for i in range(len(mi['media']['track'])):
                t = mi['media']['track'][i]
                if t['@type'] != "Audio":
                    pass
                else: 
                    if t.get('Language', "") == meta['original_language'] and "commentary" not in t.get('Title', '').lower():
                        track_num = i
                        break
            format = mi['media']['track'][track_num]['Format']
            commercial = mi['media']['track'][track_num].get('Format_Commercial', '')
            if mi['media']['track'][track_num].get('Language', '') == "zxx":
                meta['silent'] = True
            try:
                additional = mi['media']['track'][track_num]['Format_AdditionalFeatures']
                # format = f"{format} {additional}"
            except:
                additional = ""
            try:
                format_settings = mi['media']['track'][track_num]['Format_Settings']
                if format_settings in ['Explicit']:
                    format_settings = ""
            except:
                format_settings = ""
            #Channels
            channels = mi['media']['track'][track_num].get('Channels_Original', mi['media']['track'][track_num]['Channels'])
            if not str(channels).isnumeric():
                channels = mi['media']['track'][track_num]['Channels']
            try:
                channel_layout = mi['media']['track'][track_num]['ChannelLayout']
            except:
                try:
                    channel_layout = mi['media']['track'][track_num]['ChannelLayout_Original']
                except:
                    channel_layout = ""
            if "LFE" in channel_layout:
                chan = f"{int(channels) - 1}.1"
            elif channel_layout == "":
                if int(channels) <= 2:
                    chan = f"{int(channels)}.0"
                else:
                    chan = f"{int(channels) - 1}.1"
            else:
                chan = f"{channels}.0"
            
            if meta['original_language'] != 'en':
                eng, orig = False, False
                try:
                    for t in mi['media']['track']:
                        if t['@type'] != "Audio":
                            pass
                        else: 
                            audio_language = t.get('Language', '')
                            # Check for English Language Track
                            if audio_language == "en" and "commentary" not in t.get('Title', '').lower():
                                eng = True
                            # Check for original Language Track
                            if audio_language == meta['original_language'] and "commentary" not in t.get('Title', '').lower():
                                orig = True
                            # Catch Chinese / Norwegian variants
                            variants = ['zh', 'cn', 'cmn', 'no', 'nb']
                            if audio_language in variants and meta['original_language'] in variants:
                                orig = True
                    if eng and orig == True:
                        dual = "Dual-Audio"
                    elif eng == True and orig == False and meta['original_language'] not in ['zxx', 'xx', None] and meta.get('no_dub', False) == False:
                        dual = "Dubbed"
                except Exception:
                    console.print(traceback.print_exc())
                    pass
        
            
            for t in mi['media']['track']:
                if t['@type'] != "Audio":
                    pass
                else: 
                    if "commentary" in t.get('Title', '').lower():
                        has_commentary = True
        
        with open(f"{meta['base_dir']}/data/audio_config.json", 'r', encoding="utf-8") as f:
            audio_config = json.load(f)
            f.close()
            
        #Convert commercial name to naming conventions
        audio = audio_config['audio']
        audio_extra = audio_config['audio_extra']
        format_extra = audio_config['format_extra']
        format_settings_extra = audio_config['format_settings_extra']
        commercial_names = audio_config['commercial_names']
        
        search_format = True
        for key, value in commercial_names.items():
            if key in commercial:
                codec = value
                search_format = False
            if "Atmos" in commercial or format_extra.get(additional, "") == " Atmos":
                extra = " Atmos"
        if search_format:
            codec = audio.get(format, "") + audio_extra.get(additional, "")
            extra = format_extra.get(additional, "")
        format_settings = format_settings_extra.get(format_settings, "")
        if format_settings == "EX" and chan == "5.1":
            format_settings = "EX"
        else:
            format_settings = ""

        if codec == "":
            codec = format
        
        if format.startswith("DTS"):
            if additional.endswith("X"):
                codec = "DTS:X"
                chan = f"{int(channels) - 1}.1"
        if format == "MPEG Audio":
            codec = mi['media']['track'][2].get('CodecID_Hint', '')

        

        audio = f"{dual} {codec} {format_settings} {chan}{extra}"
        audio = ' '.join(audio.split())
        return audio, chan, has_commentary


    def is_3d(self, mi, bdinfo):
        if bdinfo != None:
            if bdinfo['video'][0]['3d'] != "":
                return "3D"
            else:
                return ""
        else:
            return ""

    def get_tag(self, video, meta):
        try:
            tag = guessit(video)['release_group']
            tag = f"-{tag}"
        except:
            tag = ""
        if tag == "-":
            tag = ""
        if tag[1:].lower() in ["nogroup", 'nogrp']:
            tag = ""
        return tag


    def get_source(self, type, video, path, is_disc, meta):
        try:
            try:
                source = guessit(video)['source']
            except:
                try:
                    source = guessit(path)['source']
                except:
                    source = "BluRay"
            if meta.get('manual_source', None):
                source = meta['manual_source']
            if source in ("Blu-ray", "Ultra HD Blu-ray", "BluRay", "BR") or is_disc == "BDMV":
                if type == "DISC":
                    source = "Blu-ray"
                elif type in ('ENCODE', 'REMUX'):
                    source = "BluRay"
            if is_disc == "DVD" or source in ("DVD", "dvd"):
                try:
                    if is_disc == "DVD":
                        mediainfo = MediaInfo.parse(f"{meta['discs'][0]['path']}/VTS_{meta['discs'][0]['main_set'][0][:2]}_0.IFO")
                    else:
                        mediainfo = MediaInfo.parse(video)
                    for track in mediainfo.tracks:
                        if track.track_type == "Video":
                            system = track.standard
                    if system not in ("PAL", "NTSC"):
                        raise Exception
                except:
                    try:
                        other = guessit(video)['other']
                        if "PAL" in other:
                            system = "PAL"
                        elif "NTSC" in other:
                            system = "NTSC"
                    except:
                        system = ""
                finally:
                    if system == None:
                        system = ""        
                    if type == "REMUX":
                        system = f"{system} DVD".strip()
                    source = system
            if source in ("Web", "WEB"):
                if type == "ENCODE":
                    type = "WEBRIP"
            if source in ("HD-DVD", "HD DVD", "HDDVD"):
                if is_disc == "HDDVD":
                    source = "HD DVD"
                if type in ("ENCODE", "REMUX"):
                    source = "HDDVD"
            if type in ("WEBDL", 'WEBRIP'):
                source = "Web"
            if source == "Ultra HDTV":
                source = "UHDTV"
        except Exception:
            console.print(traceback.format_exc())
            source = "BluRay"

        return source, type

    def get_uhd(self, type, guess, resolution, path):
        try:
            source = guess['Source']
            other = guess['Other']
        except:
            source = ""
            other = ""
        uhd = ""
        if source == 'Blu-ray' and other == "Ultra HD" or source == "Ultra HD Blu-ray":
            uhd = "UHD"
        elif "UHD" in path:
            uhd = "UHD"
        elif type in ("DISC", "REMUX", "ENCODE", "WEBRIP"):
            uhd = ""
            
        if type in ("DISC", "REMUX", "ENCODE") and resolution == "2160p":
            uhd = "UHD"

        return uhd

    def get_hdr(self, mi, bdinfo):
        hdr = ""
        dv = ""
        if bdinfo != None: #Disks
            hdr_mi = bdinfo['video'][0]['hdr_dv']
            if "HDR10+" in hdr_mi:
                hdr = "HDR10+"
            elif hdr_mi == "HDR10":
                hdr = "HDR"
            try:
                if bdinfo['video'][1]['hdr_dv'] == "Dolby Vision":
                    dv = "DV"
            except:
                pass
        else: 
            video_track = mi['media']['track'][1]
            try:
                hdr_mi = video_track['colour_primaries']
                if hdr_mi in ("BT.2020", "REC.2020"):
                    hdr = ""
                    hdr_format_string = video_track.get('HDR_Format_Compatibility', video_track.get('HDR_Format_String', video_track.get('HDR_Format', "")))
                    if "HDR10" in hdr_format_string:
                        hdr = "HDR"
                    if "HDR10+" in hdr_format_string:
                        hdr = "HDR10+"
                    if hdr_format_string == "" and "PQ" in (video_track.get('transfer_characteristics'), video_track.get('transfer_characteristics_Original', None)):
                        hdr = "PQ10"
                    transfer_characteristics = video_track.get('transfer_characteristics_Original', None)
                    if "HLG" in transfer_characteristics:
                        hdr = "HLG"
                    if hdr != "HLG" and "BT.2020 (10-bit)" in transfer_characteristics:
                        hdr = "WCG"
            except:
                pass

            try:
                if "Dolby Vision" in video_track.get('HDR_Format', '') or "Dolby Vision" in video_track.get('HDR_Format_String', ''):
                    dv = "DV"
            except:
                pass

        hdr = f"{dv} {hdr}".strip()
        return hdr

    def get_region(self, meta, bdinfo, region=None):
        label = bdinfo.get('label', bdinfo.get('title', bdinfo.get('path', ''))).replace('.', ' ')
        if region != None:
            region = region.upper()
        else:
            with open(f"{meta['base_dir']}/data/regions.json", 'r', encoding="utf-8") as f:
                regions = json.load(f)
            f.close() 
            for key, value in regions.items():
                if f" {key} " in label:
                    region = value
                    
        if region == None:
            region = ""
        return region

    def get_distributor(self, meta, distributor_in):
        with open(f"{meta['base_dir']}/data/distribution.json", 'r', encoding="utf-8") as json_file:
            distributor_list = json.load(json_file)
            
        distributor_out = ""
        if distributor_in not in [None, "None", ""]:
            for each in distributor_list:
                if distributor_in.upper() == each:
                    distributor_out = each
        return distributor_out


    def get_video_codec(self, bdinfo):
        codecs = {
            "MPEG-2 Video" : "MPEG-2",
            "MPEG-4 AVC Video" : "AVC",
            "MPEG-H HEVC Video" : "HEVC",
            "VC-1 Video" : "VC-1"
        }
        codec = codecs.get(bdinfo['video'][0]['codec'], "")
        return codec

    def get_video_encode(self, mi, type, bdinfo):
        video_encode = ""
        codec = ""
        bit_depth = '0'
        has_encode_settings = False
        try:
            format = mi['media']['track'][1]['Format']
            format_profile = mi['media']['track'][1].get('Format_Profile', format)
            if mi['media']['track'][1].get('Encoded_Library_Settings', None):
                has_encode_settings = True
            bit_depth = mi['media']['track'][1].get('BitDepth', '0')
        except:
            format = bdinfo['video'][0]['codec']
            format_profile = bdinfo['video'][0]['profile']
        if type in ("ENCODE", "WEBRIP"): #ENCODE or WEBRIP
            if format == 'AVC':
                codec = 'x264'
            elif format == 'HEVC':
                codec = 'x265'
        elif type in ('WEBDL', 'HDTV'): #WEB-DL
            if format == 'AVC':
                codec = 'H.264'
            elif format == 'HEVC':
                codec = 'H.265'
            
            if type == 'HDTV' and has_encode_settings == True:
                codec = codec.replace('H.', 'x')
        elif format == "VP9":
            codec = "VP9"
        elif format == "VC-1":
            codec = "VC-1"
        elif format == "AV1":
            codec = "AV1" 
        if format_profile == 'High 10':
            profile = "Hi10P"
        else:
            profile = ""
        if profile and codec:
            if profile != codec:
                video_encode = f"{profile} {codec}"
            else:
                video_encode = codec
        else:
            video_encode = format
        video_codec = format
        if video_codec == "MPEG Video":
            video_codec = f"MPEG-{mi['media']['track'][1].get('Format_Version')}"
        return video_encode, video_codec, has_encode_settings, bit_depth


    def get_edition(self, meta, title, video, bdinfo, filelist, manual_edition):
        # Normalize video string
        video = video.lower().replace('dc', '', 1)
        guess = guessit(video)
        tag = guess.get('release_group', 'NOGROUP')

        def contains_keywords(text, keywords):
            text_upper = text.upper()
            return any(re.search(re.escape(keyword), text_upper) for keyword in keywords)

        with open(f"{meta['base_dir']}/data/editions.json", 'r', encoding="utf-8") as f:
            edition_config = json.load(f)
            f.close()
        
        cuts = edition_config['cuts']
        ai_upscale_keywords = edition_config['ai_upscale_keywords']
        repack_keywords = edition_config['repack_keywords']
        ratios = edition_config['ratios']

        edition = ""
        if bdinfo:
            try:
                edition = guessit(bdinfo['label']).get('edition', "")
            except Exception:
                edition = ""
        else:
            edition = guess.get('edition', "")
            
        if isinstance(edition, list):
            edition = " ".join(edition)

        if len(filelist) == 1:
            video = os.path.basename(video)

        video = video.upper().replace('.', ' ').replace(tag, '').replace('-', '')
        cut = next((value for key, value in cuts.items() if key in video.lower()), "")
        ratio = next((value for key, value in ratios.items() if key in video.upper()), "")

        repack = next((repack_type for repack_type, keywords in repack_keywords.items() 
            if contains_keywords(video, keywords) or contains_keywords(edition, keywords) or contains_keywords(str(manual_edition), keywords)), "")
        
        if contains_keywords(edition, ai_upscale_keywords) or contains_keywords(video, ai_upscale_keywords) or contains_keywords(str(manual_edition), ai_upscale_keywords):
            edition = "AI UPSCALE " + edition

        if "HYBRID" in video.upper() and "HYBRID" not in title.upper():
            edition = "Hybrid " + edition

        edition = re.sub(r"(REPACK\d?)?(RERIP)?(PROPER)?", "", edition, flags=re.IGNORECASE).strip()

        return edition, repack, cut, ratio

    """
    Create Torrent
    """
    def create_torrent(self, meta, path, output_filename, piece_size_max):
        piece_size_max = int(piece_size_max) if piece_size_max is not None else 0
        if meta['isdir'] == True:
            os.chdir(path)
            globs = glob.glob1(path, "*.mkv") + glob.glob1(path, "*.mp4") + glob.glob1(path, "*.ts")
            no_sample_globs = []
            for file in globs:
                if not file.lower().endswith('sample.mkv') or "!sample" in file.lower():
                    no_sample_globs.append(os.path.abspath(f"{path}{os.sep}{file}"))
            if len(no_sample_globs) == 1:
                path = meta['filelist'][0]
        if meta['is_disc']:
            include, exclude = "", ""
        else:
            exclude = ["*.*", "*sample.mkv", "!sample*.*", "._*"] 
            include = ["*.mkv", "*.mp4", "*.ts"]
        torrent = Torrent(path,
            trackers = ["https://fake.tracker"],
            source = "", #unstamped for easy storage finding for reuse via hash
            private = True,
            exclude_globs = exclude or [],
            include_globs = include or [],
            creation_date = datetime.now(),
            comment = "Created by UTOPIA Upload Assistant",
            created_by = "UTOPIA Upload Assistant")
        file_size = torrent.size
        if file_size < 268435456: # 256 MiB File / 256 KiB Piece Size
            piece_size = 18
            piece_size_text = "256KiB"
        elif file_size < 1073741824:  # 1 GiB File/512 KiB Piece Size
            piece_size = 19
            piece_size_text = "512KiB"
        elif file_size < 2147483648 or piece_size_max == 1:  # 2 GiB File/1 MiB Piece Size
            piece_size = 20
            piece_size_text = "1MiB"
        elif file_size < 4294967296 or piece_size_max == 2:  # 4 GiB File/2 MiB Piece Size
            piece_size = 21
            piece_size_text = "2MiB"
        elif file_size < 8589934592 or piece_size_max == 4:  # 8 GiB File/4 MiB Piece Size
            piece_size = 22
            piece_size_text = "4MiB"
        elif file_size < 17179869184 or piece_size_max == 8:  # 16 GiB File/8 MiB Piece Size
            piece_size = 23
            piece_size_text = "8MiB"
        else: # 16MiB Piece Size
            piece_size = 24
            piece_size_text = "16MiB"
        console.print(f"[bold yellow]Creating .torrent with a piece size of {piece_size_text}... (No valid --torrenthash was provided to reuse)")
        if meta.get('torrent_creation') != None:
            torrent_creation = meta['torrent_creation']
        else:
            torrent_creation = self.config['DEFAULT'].get('torrent_creation', 'torf')
        if torrent_creation == 'torrenttools':
            args = ['torrenttools', 'create', '-a', 'https://fake.tracker', '--private', 'on', '--piece-size', str(2**piece_size), '--created-by', "L4G's Upload Assistant", '--no-cross-seed','-o', f"{meta['base_dir']}/tmp/{meta['uuid']}/{output_filename}.torrent"]
            if not meta['is_disc']:
                args.extend(['--include', r'^.*\.(mkv|mp4|ts)$'])
            args.append(path)
            err = subprocess.call(args)
            if err != 0:
                args[3] = "OMITTED"
                console.print(f"[bold red]Process execution {args} returned with error code {err}.") 
        elif torrent_creation == 'mktorrent':
            args = ['mktorrent', '-a', 'https://fake.tracker', '-p', f'-l {piece_size}', '-o', f"{meta['base_dir']}/tmp/{meta['uuid']}/{output_filename}.torrent", path]
            err = subprocess.call(args)
            if err != 0:
                args[2] = "OMITTED"
                console.print(f"[bold red]Process execution {args} returned with error code {err}.")
        else:
            torrent.piece_size = 2**piece_size
            torrent.piece_size_max = 16777216
            torrent.generate(callback=self.torf_cb, interval=5)
            torrent.write(f"{meta['base_dir']}/tmp/{meta['uuid']}/{output_filename}.torrent", overwrite=True)
            torrent.verify_filesize(path)
        console.print("[bold green].torrent created", end="\r")
        return torrent

    
    def torf_cb(self, torrent, filepath, pieces_done, pieces_total):
        if not hasattr(self, 'progress'):
            self.progress = Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.1f}%",
                TimeRemainingColumn(),
            )
            self.task = self.progress.add_task("Hashing...", total=pieces_total)
            self.progress.start()
        self.progress.update(self.task, completed=pieces_done)
        if pieces_done >= pieces_total:
            self.progress.stop()
            del self.progress

    def create_random_torrents(self, base_dir, uuid, num, path):
        manual_name = re.sub(r"[^0-9a-zA-Z\[\]\'\-]+", ".", os.path.basename(path))
        base_torrent = Torrent.read(f"{base_dir}/tmp/{uuid}/BASE.torrent")
        for i in range(1, int(num) + 1):
            new_torrent = base_torrent
            new_torrent.metainfo['info']['entropy'] = random.randint(1, 999999)
            Torrent.copy(new_torrent).write(f"{base_dir}/tmp/{uuid}/[RAND-{i}]{manual_name}.torrent", overwrite=True)

    def create_base_from_existing_torrent(self, torrentpath, base_dir, uuid):
        if os.path.exists(torrentpath):
            base_torrent = Torrent.read(torrentpath)
            base_torrent.creation_date = datetime.now()
            base_torrent.trackers = ['https://fake.tracker']
            base_torrent.comment = "Created by UTOPIA Upload Assistant"
            base_torrent.created_by = "Created by UTOPIA Upload Assistant"
            #Remove Un-whitelisted info from torrent
            for each in list(base_torrent.metainfo['info']):
                if each not in ('files', 'length', 'name', 'piece length', 'pieces', 'private', 'source'):
                    base_torrent.metainfo['info'].pop(each, None)
            for each in list(base_torrent.metainfo):
                if each not in ('announce', 'comment', 'creation date', 'created by', 'encoding', 'info'):
                    base_torrent.metainfo.pop(each, None)
            base_torrent.source = '' #unstamped for easy storage finding for reuse via hash
            base_torrent.private = True
            Torrent.copy(base_torrent).write(f"{base_dir}/tmp/{uuid}/BASE.torrent", overwrite=True)

    """
    Upload Screenshots
    """
    def upload_screens(self, meta):
        uploader = ImageUploader(self)
        uploaded_images = uploader.upload_screens(meta)
        
        return uploaded_images

    async def get_name(self, meta):
        # Simplified dictionary access with default values
        # Refactored code as is. No idea why we need that, but would asume that there some issue with some props could be empty for some corner cases
        # keys contains props, that should be checked, and if empty, added back to meta as empty string ""
        keys = ['type', 'title', 'aka', 'year', 'resolution', 'audio', 'service',
        'season', 'episode', 'part', 'repack', '3D', 'tag', 'source',
        'uhd', 'hdr', 'episode_title', 'video_codec', 'video_encode', 'edition', 'is_disc', 'region', 'dvd_size', 'search_year', 'cut', 'ration']
        for key in keys:
            if key not in meta:
                meta[key] = ""

        # Handling special cases
        meta['resolution'] = "" if meta['resolution'] == "OTHER" else meta['resolution']
        meta['season'] = "" if meta.get('no_season', False) else meta['season']
        meta['year'] = "" if meta.get('no_year', False) else meta['year']
        meta['aka'] = "" if meta.get('no_aka', False) else meta['aka']
        
        if not meta.get('source'):
            meta['source'] = meta.get('manual_source') or meta.get('is_disc') or meta['source']

        if meta['debug']:
            console.log("[cyan]get_name cat/type")
            console.log(f"CATEGORY: {meta['category']}")
            console.log(f"TYPE: {meta['type']}")
            console.log("[cyan]get_name meta:")
            console.log(meta)
            
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        config_path = os.path.join(base_dir, 'data', 'naming.json')
        
        with open(config_path, 'r', encoding="utf-8-sig") as file:
            naming_config = json.load(file)
            
        # Get configuration based on meta
        category_config = naming_config.get(meta['category'], {})
        type_config = category_config.get(meta['type'], {})
        # Check if type is DISC or REMUX
        if meta['type'] in ['DISC', 'REMUX']:
            source_config = type_config.get(meta['source'], {})
        else:
            # If type is not DISC or REMUX, use type_config directly for template and potential_missing
            source_config = type_config
    
        template = source_config.get('template', '')
        potential_missing = source_config.get('potential_missing', [])
        # Extract variables from meta for formatting
        # Format the name using the appropriate template
        format_vars = {key[1]: meta.get(key[1], '') for key in string.Formatter().parse(template) if key[1]}
        name = template.format(**format_vars)

        try:
            # Normalize whitespace in the name    
            name = ' '.join(name.split())
        except:
            # Handle exceptions by notifying the user and exiting
            console.print("[bold red]Unable to generate name. Please re-run and correct any of the following args if needed.")
            console.print(f"--category [yellow]{meta['category']}")
            console.print(f"--type [yellow]{meta['type']}")
            console.print(f"--source [yellow]{meta['source']}")
            exit()
        
        # Append tag to the name     
        name_notag = name
        name = name_notag + meta['tag']
        # Clean the filename
        clean_name = self.clean_filename(name)
        return name_notag, name, clean_name, potential_missing


    async def get_season_episode(self, video, meta):
        if meta['category'] == 'TV':
            filelist = meta['filelist']
            meta['tv_pack'] = 0
            is_daily = False
            if meta['anime'] == False:
                try:
                    if meta.get('manual_date'):
                        raise Exception
                    try:
                        guess_year = guessit(video)['year']
                    except Exception:
                        guess_year = ""
                    if guessit(video)["season"] == guess_year:
                        if f"s{guessit(video)['season']}" in video.lower():
                            season_int =  str(guessit(video)["season"])
                            season = "S" + season_int.zfill(2)
                        else:
                            season_int = "1"
                            season = "S01"
                    else:
                        season_int =  str(guessit(video)["season"])
                        season = "S" + season_int.zfill(2)

                except Exception:
                    try:
                        guess_date = meta.get('manual_date', guessit(video)['date']) if meta.get('manual_date') else guessit(video)['date']
                        season_int, episode_int = self.daily_to_tmdb_season_episode(meta.get('tmdb'), guess_date)
                        season = str(guess_date)
                        episode = ""
                        is_daily = True
                    except Exception:
                        console.print_exception()
                        season_int = "1"
                        season = "S01"
                try:
                    if is_daily != True:
                        episodes = ""
                        if len(filelist) == 1:
                            episodes = guessit(video)['episode']
                            if type(episodes) == list:
                                episode = ""
                                for item in guessit(video)["episode"]:
                                    ep = (str(item).zfill(2))
                                    episode += f"E{ep}"
                                episode_int = episodes[0]
                            else:
                                episode_int = str(episodes)
                                episode = "E" + str(episodes).zfill(2)
                        else:
                            episode = ""
                            episode_int = "0"
                            meta['tv_pack'] = 1
                except Exception:
                    episode = ""
                    episode_int = "0"
                    meta['tv_pack'] = 1
            else:
                #If Anime
                parsed = anitopy.parse(Path(video).name)
                romaji, mal_id, eng_title, seasonYear, anilist_episodes = self.get_romaji(parsed['anime_title'], meta.get('mal', None))
                if mal_id:
                    meta['mal_id'] = mal_id
                if meta.get('tmdb_manual', None) == None:
                    year = parsed.get('anime_year', str(seasonYear))
                    meta = await self.get_tmdb_id(guessit(parsed['anime_title'], {"excludes" : ["country", "language"]})['title'], year, meta, meta['category'])
                meta = await self.tmdb_other_meta(meta)
                if meta['category'] != "TV":
                    return meta
                
                tag = parsed.get('release_group', "")
                if tag != "":
                    meta['tag'] = f"-{tag}"
                if len(filelist) == 1:
                    try:
                        episodes = parsed.get('episode_number', guessit(video).get('episode', '1'))
                        if not isinstance(episodes, list) and not episodes.isnumeric():
                            episodes = guessit(video)['episode']
                        if type(episodes) == list:
                            episode = ""
                            for item in episodes:
                                ep = (str(item).zfill(2))
                                episode += f"E{ep}"
                            episode_int = episodes[0]
                        else:
                            episode_int = str(int(episodes))
                            episode = f"E{str(int(episodes)).zfill(2)}"
                    except Exception:
                        episode = "E01"
                        episode_int = "1"
                        console.print('[bold yellow]There was an error guessing the episode number. Guessing E01. Use [bold green]--episode #[/bold green] to correct if needed')
                        await asyncio.sleep(1.5)
                else:
                    episode = ""
                    episode_int = "0"
                    meta['tv_pack'] = 1
                    
                try:
                    if meta.get('season_int'):
                        season = meta.get('season_int')
                    else:
                        season = parsed.get('anime_season', guessit(video)['season'])
                    season_int = season
                    season = f"S{season.zfill(2)}"
                except Exception:
                    try:
                        if int(episode_int) >= anilist_episodes:
                            params = {
                                'id' : str(meta['tvdb_id']),
                                'origin' : 'tvdb',
                                'absolute' : str(episode_int),
                            }
                            url = "https://thexem.info/map/single"
                            response = requests.post(url, params=params).json()
                            if response['result'] == "failure":
                                raise Exception
                            if meta['debug']:
                                console.log(f"[cyan]TheXEM Absolute -> Standard[/cyan]\n{response}")
                            season_int = str(response['data']['scene']['season'])
                            season = f"S{str(response['data']['scene']['season']).zfill(2)}"
                            if len(filelist) == 1:
                                episode_int = str(response['data']['scene']['episode'])
                                episode = f"E{str(response['data']['scene']['episode']).zfill(2)}"
                        else:
                            #Get season from xem name map
                            season = "S01"
                            season_int = "1"
                            names_url = f"https://thexem.info/map/names?origin=tvdb&id={str(meta['tvdb_id'])}"
                            names_response = requests.get(names_url).json()
                            if meta['debug']:
                                console.log(f'[cyan]Matching Season Number from TheXEM\n{names_response}')
                            difference = 0
                            if names_response['result'] == "success":
                                for season_num, values in names_response['data'].items():
                                    for lang, names in values.items():
                                        if lang == "jp":
                                            for name in names:
                                                romaji_check = re.sub(r"[^0-9a-zA-Z\[\]]+", "", romaji.lower().replace(' ', ''))
                                                name_check = re.sub(r"[^0-9a-zA-Z\[\]]+", "", name.lower().replace(' ', ''))
                                                diff = SequenceMatcher(None, romaji_check, name_check).ratio()
                                                if romaji_check in name_check:
                                                    if diff >= difference:
                                                        if season_num != "all":
                                                            season_int = season_num
                                                            season = f"S{season_num.zfill(2)}"
                                                        else:
                                                            season_int = "1"
                                                            season = "S01"
                                                        difference = diff
                                        if lang == "us":
                                            for name in names:
                                                eng_check = re.sub(r"[^0-9a-zA-Z\[\]]+", "", eng_title.lower().replace(' ', ''))
                                                name_check = re.sub(r"[^0-9a-zA-Z\[\]]+", "", name.lower().replace(' ', ''))
                                                diff = SequenceMatcher(None, eng_check, name_check).ratio()
                                                if eng_check in name_check:
                                                    if diff >= difference:
                                                        if season_num != "all":
                                                            season_int = season_num
                                                            season = f"S{season_num.zfill(2)}"
                                                        else:
                                                            season_int = "1"
                                                            season = "S01"
                                                        difference = diff
                            else:
                                raise Exception
                    except Exception:
                        if meta['debug']:
                            console.print_exception()
                        try:
                            season = guessit(video)['season']
                            season_int = season
                        except Exception:
                            season_int = "1"
                            season = "S01"
                        console.print(f"[bold yellow]{meta['title']} does not exist on thexem, guessing {season}")
                        console.print(f"[bold yellow]If [green]{season}[/green] is incorrect, use --season to correct")
                        await asyncio.sleep(3)
                    
            if meta.get('manual_season', None) == None:
                meta['season'] = season
            else:
                season_int = meta['manual_season'].lower().replace('s', '')
                meta['season'] = f"S{meta['manual_season'].lower().replace('s', '').zfill(2)}"
            if meta.get('manual_episode', None) == None:
                meta['episode'] = episode
            else:
                episode_int = meta['manual_episode'].lower().replace('e', '')
                meta['episode'] = f"E{meta['manual_episode'].lower().replace('e', '').zfill(2)}"
                meta['tv_pack'] = 0
            
            meta['season_int'] = season_int
            meta['episode_int'] = episode_int

            
            meta['episode_title_storage'] = guessit(video,{"excludes" : "part"}).get('episode_title', '')
            if meta['season'] == "S00" or meta['episode'] == "E00":
                meta['episode_title'] = meta['episode_title_storage']
            
            # Guess the part of the episode (if available)
            meta['part'] = ""
            if meta['tv_pack'] == 1:
                part = guessit(os.path.dirname(video)).get('part')
                meta['part'] = f"Part {part}" if part else ""

        return meta


    def get_service(self, video, meta, tag, audio, guess_title):
        service = guessit(video).get('streaming_service', "")
        
        with open(f"{meta['base_dir']}/data/services.json", 'r', encoding="utf-8") as json_file:
            services = json.load(json_file)
        video_name = re.sub(r"[.()]", " ", video.replace(tag, '').replace(guess_title, ''))
        #TBD looks like here a bug and it's not covering MA in video name
        if "DTS-HD MA" in audio:
            video_name = video_name.replace("DTS-HD.MA.", "").replace("DTS-HD MA ", "")
        for key, value in services.items():
            if (' ' + key + ' ') in video_name and key not in guessit(video, {"excludes" : ["country", "language"]}).get('title', ''):
                service = value
            elif key == service:
                service = value
        service_longname = service
        for key, value in services.items():
            if value == service and len(key) > len(service_longname):
                service_longname = key
        if service_longname == "Amazon Prime":
            service_longname = "Amazon"
        return service, service_longname

    def stream_optimized(self, stream_opt):
        if stream_opt == True:
            stream = 1
        else:
            stream = 0
        return stream

    def is_anon(self, anon_in):
        anon = self.config['DEFAULT'].get("Anon", "False")
        if anon.lower() == "true":
            console.print("[bold red]Global ANON has been removed in favor of per-tracker settings. Please update your config accordingly.")
            time.sleep(10)
        if anon_in == True:
            anon_out = 1
        else:
            anon_out = 0
        return anon_out

    async def upload_image(self, session, url, data, headers, files):
        if headers == None and files == None:
            async with session.post(url=url, data=data) as resp:
                response = await resp.json()
                return response
        elif headers == None and files != None:
            async with session.post(url=url, data=data, files=files) as resp:
                response = await resp.json()
                return response
        elif headers != None and files == None:
            async with session.post(url=url, data=data, headers=headers) as resp:
                response = await resp.json()
                return response
        else:
            async with session.post(url=url, data=data, headers=headers, files=files) as resp:
                response = await resp.json()
                return response
            
    
    def clean_filename(self, name):
        invalid = r'<>:"/\|?*'
        for char in invalid:
            name = name.replace(char, '-')
        return name

    
    async def gen_desc(self, meta):
        desclink = meta.get('desclink', None)
        descfile = meta.get('descfile', None)
        description_path = f"{meta['base_dir']}/tmp/{meta['uuid']}/DESCRIPTION.txt"
        desc_source = []
        with open(description_path, 'w', newline="", encoding='utf8') as description:
            description.seek(0)
            if (desclink, descfile, meta['desc']) == (None, None, None):
                if len(desc_source) != 1:
                    desc_source = None
                else:
                    desc_source = desc_source[0]

            if meta.get('desc_template', None) != None:
                from jinja2 import Template
                with open(f"{meta['base_dir']}/data/templates/{meta['desc_template']}.txt", 'r', encoding='utf-8') as f:
                    desc_templater = Template(f.read())
                    template_desc = desc_templater.render(meta)
                    if template_desc.strip() != "":
                        description.write(template_desc)
                        description.write("\n")

            if meta['nfo'] != False:
                description.write("[code]")
                nfo = glob.glob("*.nfo")[0]
                description.write(open(nfo, 'r', encoding="utf-8").read())
                description.write("[/code]")
                description.write("\n")
                meta['description'] = "CUSTOM"
            if desclink != None:
                parsed = urllib.parse.urlparse(desclink.replace('/raw/', '/'))
                split = os.path.split(parsed.path)
                if split[0] != '/':
                    raw = parsed._replace(path=f"{split[0]}/raw/{split[1]}")
                else:
                    raw = parsed._replace(path=f"/raw{parsed.path}")
                raw = urllib.parse.urlunparse(raw)
                description.write(requests.get(raw).text)
                description.write("\n")
                meta['description'] = "CUSTOM"
                
            if descfile != None:
                if os.path.isfile(descfile) == True:
                    text = open(descfile, 'r', encoding='utf-8').read()
                    description.write(text)
                meta['description'] = "CUSTOM"
            if meta['desc'] != None:
                description.write(meta['desc'])
                description.write("\n")
                meta['description'] = "CUSTOM"
            description.write("\n")
        return meta
        
    async def tag_override(self, meta):
        with open(f"{meta['base_dir']}/data/tags.json", 'r', encoding="utf-8") as f:
            tags = json.load(f)
            f.close()
        
        for tag in tags:
            value = tags.get(tag)
            if value.get('in_name', "") == tag and tag in meta['path']:
                meta['tag'] = f"-{tag}"
            if meta['tag'][1:] == tag:
                for key in value:
                    if key == 'type':
                        if meta[key] == "ENCODE":
                            meta[key] = value.get(key)
                        else:
                            pass
                    elif key == 'personalrelease':
                        meta[key] = bool(value.get(key, False))
                    elif key == 'template':
                        meta['desc_template'] = value.get(key)
                    else:
                        meta[key] = value.get(key)
        return meta
    
    async def get_imdb_aka(self, imdb_id):
        if imdb_id == "0":
            return "", None
        ia = Cinemagoer()
        result = ia.get_movie(imdb_id.replace('tt', ''))
        
        original_language = result.get('language codes')
        if isinstance(original_language, list):
            if len(original_language) > 1:
                original_language = None
            elif len(original_language) == 1:
                original_language = original_language[0]
        aka = result.get('original title', result.get('localized title', "")).replace(' - IMDb', '').replace('\u00ae', '')
        if aka != "":
            aka = f" AKA {aka}"
        return aka, original_language

    async def get_dvd_size(self, discs):
        sizes = []
        dvd_sizes = []
        for each in discs:
            sizes.append(each['size'])
        grouped_sizes = [list(i) for j, i in itertools.groupby(sorted(sizes))]
        for each in grouped_sizes:
            if len(each) > 1:
                dvd_sizes.append(f"{len(each)}x{each[0]}")
            else:
                dvd_sizes.append(each[0])
        dvd_sizes.sort()
        compact = " ".join(dvd_sizes)
        return compact
    

    def get_tmdb_imdb_from_mediainfo(self, mediainfo, category, is_disc, tmdbid, imdbid):
        if not is_disc:
            if mediainfo['media']['track'][0].get('extra'):
                extra = mediainfo['media']['track'][0]['extra']
                for each in extra:
                    if each.lower().startswith('tmdb'):
                        parser = Args(config=self.config)
                        category, tmdbid = parser.parse_tmdb_id(id = extra[each], category=category)
                    if each.lower().startswith('imdb'):
                        try:
                            imdbid = str(int(extra[each].replace('tt', ''))).zfill(7)
                        except Exception:
                            pass
        return category, tmdbid, imdbid


    def daily_to_tmdb_season_episode(self, tmdbid, date):
        show = tmdb.TV(tmdbid)
        seasons = show.info().get('seasons')
        season = '1'
        episode = '1'
        date = datetime.fromisoformat(str(date))
        for each in seasons:
            air_date = datetime.fromisoformat(each['air_date'])
            if air_date <= date:
                season = str(each['season_number'])
        season_info = tmdb.TV_Seasons(tmdbid, season).info().get('episodes')
        for each in season_info:
            if str(each['air_date']) == str(date):
                episode = str(each['episode_number'])
                break
        else:
            console.print(f"[yellow]Unable to map the date ([bold yellow]{str(date)}[/bold yellow]) to a Season/Episode number")
        return season, episode

    async def get_imdb_info(self, imdbID, meta):
        imdb_info = {}
        if int(str(imdbID).replace('tt', '')) != 0:
            ia = Cinemagoer()
            info = ia.get_movie(imdbID)
            ia.update(info, ['technical'])
            imdb_info['title'] = info.get('title')
            imdb_info['year'] = info.get('year')
            imdb_info['aka'] = info.get('original title', info.get('localized title', imdb_info['title'])).replace(' - IMDb', '')
            imdb_info['type'] = info.get('kind')
            imdb_info['imdbID'] = info.get('imdbID')
            imdb_info['runtime'] = info.get('runtimes', ['0'])[0]
            imdb_info['cover'] = info.get('full-size cover url', '').replace(".jpg", "._V1_FMjpg_UX750_.jpg")
            imdb_info['plot'] = info.get('plot', [''])[0]
            imdb_info['genres'] = ', '.join(info.get('genres', ''))
            imdb_info['soundmix'] = info.get('sound mix')
            imdb_info['original_language'] = info.get('language codes')
            if isinstance(imdb_info['original_language'], list):
                if len(imdb_info['original_language']) > 1:
                    imdb_info['original_language'] = None
                elif len(imdb_info['original_language']) == 1:
                    imdb_info['original_language'] = imdb_info['original_language'][0]
            if imdb_info['cover'] == '':
                imdb_info['cover'] = meta.get('poster', '')
            if len(info.get('directors', [])) >= 1:
                imdb_info['directors'] = []
                for director in info.get('directors'):
                    imdb_info['directors'].append(f"nm{director.getID()}")
        else:
            imdb_info = {
                'title' : meta['title'],
                'year' : meta['year'],
                'aka' : '',
                'type' : None,
                'runtime' : meta.get('runtime', '60'),
                'cover' : meta.get('poster'),
            }
            if len(meta.get('tmdb_directors', [])) >= 1:
                imdb_info['directors'] = meta['tmdb_directors']

        return imdb_info
        

    async def search_imdb(self, filename, search_year):
        imdbID = '0'
        ia = Cinemagoer()
        search = ia.search_movie(filename)
        for movie in search:
            if filename in movie.get('title', ''):
                if movie.get('year') == search_year:
                    imdbID = str(movie.movieID).replace('tt', '')
        return imdbID


    async def imdb_other_meta(self, meta):
        imdb_info = meta['imdb_info'] = await self.get_imdb_info(meta['imdb_id'], meta)
        meta['title'] = imdb_info['title']
        meta['year'] = imdb_info['year']
        meta['aka'] = imdb_info['aka']
        meta['poster'] = imdb_info['cover']
        meta['original_language'] = imdb_info['original_language']
        meta['overview'] = imdb_info['plot']

        difference = SequenceMatcher(None, meta['title'].lower(), meta['aka'][5:].lower()).ratio()
        if difference >= 0.9 or meta['aka'][5:].strip() == "" or meta['aka'][5:].strip().lower() in meta['title'].lower():
            meta['aka'] = ""
        if f"({meta['year']})" in meta['aka']:
            meta['aka'] = meta['aka'].replace(f"({meta['year']})", "").strip()
        return meta

    async def search_tvmaze(self, filename, year, imdbID, tvdbID):
        tvdbID = int(tvdbID)
        tvmazeID = 0
        lookup = False
        show = None
        if imdbID == None:
            imdbID = '0'
        if tvdbID == None:
            tvdbID = 0
        if int(tvdbID) != 0:
            params = {
                "thetvdb" : tvdbID
            }
            url = "https://api.tvmaze.com/lookup/shows"
            lookup = True
        elif int(imdbID) != 0:
            params = {
                "imdb" : f"tt{imdbID}"
            }
            url = "https://api.tvmaze.com/lookup/shows"
            lookup = True
        else:
            params = {
                "q" : filename
            }
            url = f"https://api.tvmaze.com/search/shows"
        resp = requests.get(url=url, params=params)
        if resp.ok:
            resp = resp.json()
            if resp == None:
                return tvmazeID, imdbID, tvdbID
            if lookup == True:
                show = resp
            else:
                if year not in (None, ''):
                    for each in resp:
                        premier_date = each['show'].get('premiered', '')
                        if premier_date != None:
                            if premier_date.startswith(str(year)):
                                show = each['show']
                elif len(resp) >= 1:
                    show = resp[0]['show']
            if show != None:
                tvmazeID = show.get('id')
                if int(imdbID) == 0:
                    if show.get('externals', {}).get('imdb', '0') != None:
                        imdbID = str(show.get('externals', {}).get('imdb', '0')).replace('tt', '')
                if int(tvdbID) == 0:
                    if show.get('externals', {}).get('tvdb', '0') != None:
                        tvdbID = show.get('externals', {}).get('tvdb', '0')
        return tvmazeID, imdbID, tvdbID
