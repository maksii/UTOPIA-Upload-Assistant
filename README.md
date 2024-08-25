# UTOPIA Upload Assistant

This is a fork of L4G's Upload Assistant for the UTOPIA tracker. The main differences between this version and the original are:

* Merged updated changes from [Audionut](https://github.com/Audionut/Upload-Assistant), [L4GSP1KE](https://github.com/L4GSP1KE/Upload-Assistant) repos [z-ink](https://github.com/z-ink/Uploadrr)
* Utopia-specific configuration
* Modified naming rules to comply with tracker requirements
* Removed configuration and code specific to other trackers, making this version focused on UTOPIA only.
* Migrated hardcoded Python configuration (.py file) to a JSON-based approach.
* Integration with PyInstaller for building a frozen executable
* Docker - not tested
* Removed Discord-related code from the project.(not in roadmap right now. will be restored only after full project stabilization and testing)
* naming rules refactored and moved to json configuration

If you are looking for the latest supported version of the original L4G's Upload Assistant, please use [Audionut/Upload-Assistant](https://github.com/Audionut/Upload-Assistant).

## Info

Check other repos for installation steps. Only difference in configuration that should be done via json files.
Check utopia forum for more information and support.

### Building the Frozen Executable using PyInstaller

To build the frozen executable, follow these steps:

1. Install PyInstaller using pip: `pip install pyinstaller`
2. Run the following command to build the executable: `pyinstaller upload.spec`