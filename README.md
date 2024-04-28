# UTOPIA Upload Assistant

This is a fork of L4G's Upload Assistant for the UTOPIA tracker. The main differences between this version and the original are:

* Utopia-specific configuration
* Modified naming rules to comply with tracker requirements
* Removed configuration and code specific to other trackers, making this version focused on UTOPIA only.
* Migrated hardcoded Python configuration (.py file) to a JSON-based approach.
* Integration with PyInstaller for building a frozen executable
* Removed all Docker-related configurations from the project(not in roadmap right now)
* Removed Discord-related code from the project.(not in roadmap right now)

## PyInstaller

### Building the Frozen Executable using PyInstaller

To build the frozen executable, follow these steps:

1. Install PyInstaller using pip: `pip install pyinstaller`

#### freez branch
2. Run the following command to build the executable: `pyinstaller upload.spec`
#### other branch
2. Copy the `upload.spec` file to your current branch
3. update upload.py as per freez branch changes
4. Run the following command to build the executable: `pyinstaller upload.spec`

Note: Make sure you have the necessary dependencies installed before building.

### Additional Steps

After building the executable, perform the following steps:

1. Add `config.json` and `tags.json` files to the `dist/data` directory
2. Run the built executable with the `-help` flag to test its functionality: `dist/upload.exe -help`
