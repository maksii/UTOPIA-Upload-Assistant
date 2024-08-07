import requests
from src.args import Args
from src.clients import Clients
from src.prep import Prep
from src.trackers.COMMON import COMMON
from src.trackers.UTOPIA import UTOPIA
import json
from pathlib import Path
import asyncio
import os
import sys
import re
import platform
import shutil
import glob
import subprocess
import traceback
import time
import random
from packaging.version import Version

from src.console import console
from rich.markdown import Markdown
from rich.style import Style
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.rule import Rule
from rich.console import Group
from rich.progress import Progress, TimeRemainingColumn
from difflib import SequenceMatcher
import bencodepy as bencode
from urllib.parse import urlparse, parse_qs
import importlib



import traceback

# Determine if the application is running as a frozen executable or as a script
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(base_dir, 'data', 'config.json')

# Load the configuration file
try:
    with open(config_path, 'r', encoding="utf-8-sig") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: Configuration file not found at {config_path}")
    sys.exit(1)


client = Clients(config=config)
parser = Args(config)

async def do_the_thing(base_dir):
    meta = dict()
    meta['base_dir'] = base_dir
    paths = []
    for each in sys.argv[1:]:
        if os.path.exists(each):
            paths.append(os.path.abspath(each))
        else:
            break
    meta, help, before_args = parser.parse(tuple(' '.join(sys.argv[1:]).split(' ')), meta)
    if meta['cleanup'] and os.path.exists(f"{base_dir}/tmp"):
        shutil.rmtree(f"{base_dir}/tmp")
        console.print("[bold green]Sucessfully emptied tmp directory")
    if not meta['path']:
        exit(0)
    path = meta['path']
    path = os.path.abspath(path)
    if path.endswith('"'):
        path = path[:-1]
    queue = []
    if os.path.exists(path):
            meta, help, before_args = parser.parse(tuple(' '.join(sys.argv[1:]).split(' ')), meta)
            queue = [path]
    else:
        # Search glob if dirname exists
        if os.path.exists(os.path.dirname(path)) and len(paths) <= 1:
            escaped_path = path.replace('[', '[[]')
            globs = glob.glob(escaped_path)
            queue = globs
            if len(queue) != 0:
                md_text = "\n - ".join(queue)
                console.print("\n[bold green]Queuing these files:[/bold green]", end='')
                console.print(Markdown(f"- {md_text.rstrip()}\n\n", style=Style(color='cyan')))
                console.print("\n\n")
            else:
                console.print(f"[red]Path: [bold red]{path}[/bold red] does not exist")
                
        elif os.path.exists(os.path.dirname(path)) and len(paths) != 1:
            queue = paths
            md_text = "\n - ".join(queue)
            console.print("\n[bold green]Queuing these files:[/bold green]", end='')
            console.print(Markdown(f"- {md_text.rstrip()}\n\n", style=Style(color='cyan')))
            console.print("\n\n")
        elif not os.path.exists(os.path.dirname(path)):
            split_path = path.split()
            p1 = split_path[0]
            for i, each in enumerate(split_path):
                try:
                    if os.path.exists(p1) and not os.path.exists(f"{p1} {split_path[i+1]}"):
                        queue.append(p1)
                        p1 = split_path[i+1]
                    else:
                        p1 += f" {split_path[i+1]}"
                except IndexError:
                    if os.path.exists(p1):
                        queue.append(p1)
                    else:
                        console.print(f"[red]Path: [bold red]{p1}[/bold red] does not exist")
            if len(queue) >= 1:
                md_text = "\n - ".join(queue)
                console.print("\n[bold green]Queuing these files:[/bold green]", end='')
                console.print(Markdown(f"- {md_text.rstrip()}\n\n", style=Style(color='cyan')))
                console.print("\n\n")
            
        else:
            # Add Search Here
            console.print(f"[red]There was an issue with your input. If you think this was not an issue, please make a report that includes the full command used.")
            exit()


    base_meta = {k: v for k, v in meta.items()}
    for path in queue:
        meta = {k: v for k, v in base_meta.items()}
        meta['path'] = path
        meta['uuid'] = None
        try:
            with open(f"{base_dir}/tmp/{os.path.basename(path)}/meta.json") as f:
                saved_meta = json.load(f)
                for key, value in saved_meta.items():
                    overwrite_list = [
                        'trackers', 'dupe', 'debug', 'anon', 'category', 'type', 'screens', 'nohash', 'manual_edition', 'imdb', 'tmdb_manual', 'mal', 'manual', 
                        'hdb', 'ptp', 'blu', 'no_season', 'no_aka', 'no_year', 'no_dub', 'no_tag', 'no_seed', 'client', 'desclink', 'descfile', 'desc', 'draft', 'region', 'freeleech', 
                        'personalrelease', 'unattended', 'season', 'episode', 'torrent_creation', 'qbit_tag', 'qbit_cat', 'skip_imghost_upload', 'imghost', 'manual_source', 'webdv', 'hardcoded-subs'
                    ]
                    if meta.get(key, None) != value and key in overwrite_list:
                        saved_meta[key] = meta[key]
                meta = saved_meta
                f.close()
        except FileNotFoundError:
            pass
        console.print(f"[green]Gathering info for {os.path.basename(path)}")
        if meta['imghost'] == None:
            meta['imghost'] = config['DEFAULT']['img_host_1']
        if not meta['unattended']:
            ua = config['DEFAULT'].get('auto_mode', False)
            if str(ua).lower() == "true":
                meta['unattended'] = True
                console.print("[yellow]Running in Auto Mode")
        prep = Prep(screens=meta['screens'], img_host=meta['imghost'], config=config)
        meta = await prep.gather_prep(meta=meta, mode='cli') 
        meta['name_notag'], meta['name'], meta['clean_name'], meta['potential_missing'] = await prep.get_name(meta)

        if meta.get('image_list', False) in (False, []) and meta.get('skip_imghost_upload', False) == False:
            return_dict = {}
            meta['image_list'], dummy_var = prep.upload_screens(meta, meta['screens'], 1, 0, meta['screens'],[], return_dict)
            if meta['debug']:
                console.print(meta['image_list'])
            # meta['uploaded_screens'] = True
        elif meta.get('skip_imghost_upload', False) == True and meta.get('image_list', False) == False:
            meta['image_list'] = []

        if not os.path.exists(os.path.abspath(f"{meta['base_dir']}/tmp/{meta['uuid']}/BASE.torrent")):
            reuse_torrent = None
            if meta.get('rehash', False) == False:
                reuse_torrent = await client.find_existing_torrent(meta)
                if reuse_torrent != None:
                    prep.create_base_from_existing_torrent(reuse_torrent, meta['base_dir'], meta['uuid'])
            if meta['nohash'] == False and reuse_torrent == None:
                prep.create_torrent(meta, Path(meta['path']), "BASE", meta.get('piece_size_max', 0))
            if meta['nohash']:
                meta['client'] = "none"
        elif os.path.exists(os.path.abspath(f"{meta['base_dir']}/tmp/{meta['uuid']}/BASE.torrent")) and meta.get('rehash', False) == True and meta['nohash'] == False:
            prep.create_torrent(meta, Path(meta['path']), "BASE", meta.get('piece_size_max', 0))
        if int(meta.get('randomized', 0)) >= 1:
            prep.create_random_torrents(meta['base_dir'], meta['uuid'], meta['randomized'], meta['path'])
            
        if meta.get('trackers', None) != None:
            trackers = meta['trackers']
        else:
            trackers = config['TRACKERS']['default_trackers']
        if "," in trackers:
            trackers = trackers.split(',')
        with open (f"{meta['base_dir']}/tmp/{meta['uuid']}/meta.json", 'w') as f:
            json.dump(meta, f, indent=4)
            f.close()
        confirm = get_confirmation(meta)  
        while not confirm:
            # help.print_help()
            console.print("Input args that need correction e.g.(--tag NTb --category tv --tmdb 12345)")  
            console.print("Enter 'skip' if no correction needed", style="dim")
            editargs = Prompt.ask("")
            if editargs.lower() == 'skip':
                break
            elif editargs == '':
                console.print("Invalid input. Please try again or type 'skip' to pass.", style="dim")
            else:
                editargs = (meta['path'],) + tuple(editargs.split())
                if meta['debug']:
                    editargs = editargs + ("--debug",)
                meta, help, before_args = parser.parse(editargs, meta)
                meta['edit'] = True
                meta = await prep.gather_prep(meta=meta, mode='cli') 
                meta['name_notag'], meta['name'], meta['clean_name'], meta['potential_missing'] = await prep.get_name(meta)
                confirm = get_confirmation(meta)
                if confirm:
                    break

        if not isinstance(trackers, list):
            trackers = [trackers]
        trackers = [s.strip().upper() for s in trackers]
        if meta.get('manual', False):
            trackers.insert(0, "MANUAL")
        


        ####################################
        #######  Upload to Trackers  #######
        ####################################
        common = COMMON(config=config)
        api_trackers = ['UTOPIA']
        http_trackers = ['HDB', 'TTG', 'FL', 'PTER', 'HDT', 'MTV']
        tracker_class_map = {'UTOPIA' : UTOPIA}

        for tracker in trackers:
            if meta['name'].endswith('DUPE?'):
                meta['name'] = meta['name'].replace(' DUPE?', '')
            tracker = tracker.replace(" ", "").upper().strip()
            if meta['debug']:
                debug = "(DEBUG)"
            else:
                debug = ""
            
            if tracker in api_trackers:
                tracker_class = tracker_class_map[tracker](config=config)
                if meta['unattended']:
                    upload_to_tracker = True
                else:
                    upload_to_tracker = Confirm.ask(f"Upload to {tracker_class.tracker}? {debug}")
                if upload_to_tracker:
                    console.print(f"Uploading to {tracker_class.tracker}")
                    if check_banned_group(tracker_class.tracker, tracker_class.banned_groups, meta):
                        continue
                    dupes = await tracker_class.search_existing(meta)
                    dupes = await common.filter_dupes(dupes, meta)
                    # note BHDTV does not have search implemented.
                    meta, skipped = dupe_check(dupes, meta)
                    if meta['upload'] == True:
                        await tracker_class.upload(meta)
                        if tracker == 'SN':
                            await asyncio.sleep(16)
                        await client.add_to_client(meta, tracker_class.tracker)
            
            if tracker in http_trackers:
                tracker_class = tracker_class_map[tracker](config=config)
                if meta['unattended']:
                    upload_to_tracker = True
                else:
                    upload_to_tracker = Confirm.ask(f"Upload to {tracker_class.tracker}? {debug}", choices=["y", "N"])
                if upload_to_tracker:
                    console.print(f"Uploading to {tracker}")
                    if check_banned_group(tracker_class.tracker, tracker_class.banned_groups, meta):
                        continue
                    if await tracker_class.validate_credentials(meta) == True:
                        dupes = await tracker_class.search_existing(meta)
                        dupes = await common.filter_dupes(dupes, meta)
                        meta, skipped = dupe_check(dupes, meta)
                        if meta['upload'] == True:
                            await tracker_class.upload(meta)
                            await client.add_to_client(meta, tracker_class.tracker)

            if tracker == "MANUAL":
                if meta['unattended']:                
                    do_manual = True
                else:
                    do_manual = Confirm.ask(f"Get files for manual upload?", default=True)
                if do_manual:
                    for manual_tracker in trackers:
                        if manual_tracker != 'MANUAL':
                            manual_tracker = manual_tracker.replace(" ", "").upper().strip()
                            tracker_class = tracker_class_map[manual_tracker](config=config)
                            if manual_tracker in api_trackers:
                                await common.unit3d_edit_desc(meta, tracker_class.tracker, tracker_class.signature)
                            else:
                                await tracker_class.edit_desc(meta)
                    url = await prep.package(meta)
                    if url == False:
                        console.print(f"[yellow]Unable to upload prep files, they can be found at `tmp/{meta['uuid']}")
                    else:
                        console.print(f"[green]{meta['name']}")
                        console.print(f"[green]Files can be found at: [yellow]{url}[/yellow]")  

def get_confirmation(meta):
    if meta['debug']:
        console.print("[bold red]DEBUG: True")
    console.print(f"Prep material saved to {meta['base_dir']}/tmp/{meta['uuid']}")
    console.print()    
    db_info = [
        f"[bold]Title[/bold]: {meta['title']} ({meta['year']})\n",
        f"[bold]Overview[/bold]: {meta['overview']}\n",
        f"[bold]Category[/bold]: {meta['category']}\n",
    ]
    if int(meta.get('tmdb', 0)) != 0:
        db_info.append(f"TMDB: https://www.themoviedb.org/{meta['category'].lower()}/{meta['tmdb']}")
    if int(meta.get('imdb_id', '0')) != 0:
        db_info.append(f"IMDB: https://www.imdb.com/title/tt{meta['imdb_id']}")
    if int(meta.get('tvdb_id', '0')) != 0:
        db_info.append(f"TVDB: https://www.thetvdb.com/?id={meta['tvdb_id']}&tab=series")
    if int(meta.get('mal_id', 0)) != 0:
        db_info.append(f"MAL : https://myanimelist.net/anime/{meta['mal_id']}")

    console.print(Panel("\n".join(db_info), title="Database Info", border_style="bold yellow"))
    console.print()
    if int(meta.get('freeleech', '0')) != 0:
        console.print(f"[bold]Freeleech[/bold]: {meta['freeleech']}")
    if meta['tag'] == "":
            tag = ""
    else:
        tag = f" / {meta['tag'][1:]}"
    if meta['is_disc'] == "DVD":
        res = meta['source']
    else:
        res = meta['resolution']

    console.print(Text(f" {res} / {meta['type']}{tag}", style="bold"))
    if meta.get('personalrelease', False) == True:
        console.print("[bright_magenta]Personal Release!")
    console.print()
    if not meta.get('unattended', False):
        get_missing(meta)
        ring_the_bell = "\a" if config['DEFAULT'].get("sfx_on_prompt", True) == True else "" # \a rings the bell
        console.print(f"[bold yellow]Is this correct?{ring_the_bell}") 
        console.print(f"[bold]Name[/bold]: {meta['name']}")
        confirm = Confirm.ask(" Correct?")
    else:
        console.print(f"[bold]Name[/bold]: {meta['name']}")
        confirm = True
    return confirm

def dupe_check(dupes, meta):
    if not dupes:
        console.print("[green]No dupes found")
        meta['upload'] = True   
        return meta, False  # False indicates not skipped

    table = Table(
        title="Are these dupes?",
        title_justify="center",
        show_header=True,
        header_style="bold underline",
        expand=True,
        show_lines=False,
        box=None
    )

    table.add_column("Name")
    table.add_column("Size", justify="center")

    for name, size in dupes.items():
        try:
            if "GB" in str(size).upper():
                size_gb = str(size).upper()
            else:
                size = int(size)
                if size > 0:
                    size_gb = str(round(size / (1024 ** 3), 2)) + " GB"  # Convert size to GB
                else:
                    size_gb = "N/A"
        except ValueError:
            size_gb = "N/A"
        table.add_row(name, f"[magenta]{size_gb}[/magenta]")

    console.print()
    console.print(table)
    console.print()

    def preprocess_string(text):
        text = re.sub(r'\[[a-z]{3}\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[^\w\s]', '', text)
        text = text.lower()
        return text

    def handle_similarity(similarity, meta):
        if similarity == 1.0:
            console.print(f"[red]Found exact match dupe.[dim](byte-for-byte)[/dim] Aborting..")
            meta['upload'] = False
            return meta, True  # True indicates skipped
        elif meta['unattended']:
            console.print(f"[red]Found potential dupe with {similarity * 100:.2f}% similarity. Aborting.")
            meta['upload'] = False
            return meta, True  # True indicates skipped
        else:
            upload = Confirm.ask(" Upload Anyways?")
            if not upload:
                meta['upload'] = False
                return meta, True  # True indicates skipped
        return meta, False  # False indicates not skipped

    similarity_threshold = max(90.00 / 100, 0.70)
    size_tolerance = max(min(30, 100), 1) / 100

    cleaned_meta_name = preprocess_string(meta['clean_name'])

    for name, dupe_size in dupes.items():
        if isinstance(dupe_size, str) and "GB" in dupe_size:
            dupe_size = float(dupe_size.replace(" GB", "")) * (1024 ** 3)  # Convert GB to bytes
        elif isinstance(dupe_size, (int, float)) and dupe_size != 0:
            meta_size = meta.get('content_size')
            if meta_size is None:
                meta_size = extract_size_from_torrent(meta['base_dir'], meta['uuid'])
            dupe_size = int(dupe_size)   
            if abs(meta_size - size) <= size_tolerance * meta_size:
                cleaned_dupe_name = preprocess_string(name)
                similarity = SequenceMatcher(None, cleaned_meta_name, cleaned_dupe_name).ratio()
                if similarity >= similarity_threshold:
                    meta, skipped = handle_similarity(similarity, meta)
                    if skipped:
                        return meta, True  # True indicates skipped
        else:
            cleaned_dupe_name = preprocess_string(name)
            similarity = SequenceMatcher(None, cleaned_meta_name, cleaned_dupe_name).ratio()
            if similarity >= similarity_threshold:
                meta, skipped = handle_similarity(similarity, meta)
                if skipped:
                    return meta, True  # True indicates skipped

    console.print("[yellow]No dupes found above the similarity threshold. Uploading anyways.")
    meta['upload'] = True
    return meta, False  # False indicates not skipped

def extract_size_from_torrent(base_dir, uuid):
    torrent_path = f"{base_dir}/tmp/{uuid}/BASE.torrent"
    with open(torrent_path, 'rb') as f:
        torrent_data = bencode.decode(f.read())
    
    info = torrent_data[b'info']
    if b'files' in info:
        # Multi-file torrent
        return sum(file[b'length'] for file in info[b'files'])
    else:
        # Single-file torrent
        return info[b'length']

# Return True if banned group
def check_banned_group(tracker, banned_group_list, meta):
    if meta['tag'] == "":
        return False
    else:
        q = False
        for tag in banned_group_list:
            if isinstance(tag, list):
                if meta['tag'][1:].lower() == tag[0].lower():
                    console.print(f"[bold yellow]{meta['tag'][1:]}[/bold yellow][bold red] was found on [bold yellow]{tracker}'s[/bold yellow] list of banned groups.")
                    console.print(f"[bold red]NOTE: [bold yellow]{tag[1]}")
                    q = True
            else:
                if meta['tag'][1:].lower() == tag.lower():
                    console.print(f"[bold yellow]{meta['tag'][1:]}[/bold yellow][bold red] was found on [bold yellow]{tracker}'s[/bold yellow] list of banned groups.")
                    q = True
        if q:
            if meta.get('unattended', False) or not Confirm.ask("[bold red] Upload Anyways?"):
                return True
    return False

def get_missing(meta):
    info_notes = {
        'edition' : 'Special Edition/Release',
        'description' : "Please include Remux/Encode Notes if possible (either here or edit your upload)",
        'service' : "WEB Service e.g.(AMZN, NF)",
        'region' : "Disc Region",
        'imdb' : 'IMDb ID (tt1234567)',
        'distributor' : "Disc Distributor e.g.(BFI, Criterion, etc)"
    }
    missing = []
    if meta.get('imdb_id', '0') == '0':
        meta['imdb_id'] = '0'
        meta['potential_missing'].append('imdb_id')
    if len(meta['potential_missing']) > 0:
        for each in meta['potential_missing']:
            if str(meta.get(each, '')).replace(' ', '') in ["", "None", "0"]:
                if each == "imdb_id":
                    each = 'imdb' 
                missing.append(f"--{each} | {info_notes.get(each)}")
    if missing != []:
        console.print(Rule("Potentially missing information", style="bold yellow"))
        for each in missing:
            if each.split('|')[0].replace('--', '').strip() in ["imdb"]:
                console.print(Text(each, style="bold red"))
            else:
                console.print(each)

    console.print()
    return

def list_directory(directory):
    items = []
    for file in os.listdir(directory):
        if not file.startswith('.'):
            items.append(os.path.abspath(os.path.join(directory, file)))
    return items

def main():
    pyver = platform.python_version_tuple()
    if int(pyver[0]) != 3:
        console.print("[bold red]Python 2 Detected, please use Python 3")
        exit()
    elif int(pyver[1]) <= 6:
        console.print("[bold red]Python <= 3.6 Detected, please use Python >= 3.7")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(do_the_thing(base_dir))
    else:
        asyncio.run(do_the_thing(base_dir))

import asyncio
import multiprocessing
import platform
from multiprocessing import set_start_method, freeze_support
if __name__ == '__main__':
    freeze_support()
    #set_start_method('spawn')
    main()
    