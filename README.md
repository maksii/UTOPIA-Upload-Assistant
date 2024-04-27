# UTOPIA Upload Assistant

Fork of L4G's Upload Assistant for UTOPIA tracker.

Main differences:

- utopia config
- namig rules change, as per tracker rules
- other tracker and tracker specific logic removed
- docker config removed
- config changed to json
- PyInstaller 

## PyInstaller

Steps to build freeze from other branches

use code from uplod.py to update to json and multiprocessing
pip install pyinstaller
copy upload.spec to brach
pyinstaller upload.spec

add config.json and tags.json to dist/data

dist>upload.exe -help