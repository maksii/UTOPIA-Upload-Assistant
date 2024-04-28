# UTOPIA Upload Assistant

This is a fork of L4G's Upload Assistant for the UTOPIA tracker. The main differences between this version and the original are:

* Merged updated changes from [Audionut](https://github.com/Audionut/Upload-Assistant) and [L4GSP1KE](https://github.com/L4GSP1KE/Upload-Assistant) repos
* Utopia-specific configuration
* Modified naming rules to comply with tracker requirements
* Removed configuration and code specific to other trackers, making this version focused on UTOPIA only.
* Migrated hardcoded Python configuration (.py file) to a JSON-based approach.
* Integration with PyInstaller for building a frozen executable
* Removed all Docker-related configurations from the project(not in roadmap right now. will be restored only after full project stabilization and testing)
* Removed Discord-related code from the project.(not in roadmap right now. will be restored only after full project stabilization and testing)
* naming rules refactored and moved to json configutation

If you are looking for the latest supported version of the original L4G's Upload Assistant, please use [Audionut/Upload-Assistant](https://github.com/Audionut/Upload-Assistant).

## PyInstaller

### Building the Frozen Executable using PyInstaller

To build the frozen executable, follow these steps:

#### Freez Branch

1. Install PyInstaller using pip: `pip install pyinstaller`
2. Run the following command to build the executable: `pyinstaller upload.spec`

#### Other Branch

1. Copy the `upload.spec` file to your current branch
2. Update `upload.py` as per freez branch changes
3. Run the following command to build the executable: `pyinstaller upload.spec`

Note: Make sure you have the necessary dependencies installed before building.

### Additional Steps

After building the executable, perform the following steps:

1. Add `config.json` and `tags.json` files to the `dist/data` directory
2. Run the built executable with the `-help` flag to test its functionality: `dist/upload.exe -help`
