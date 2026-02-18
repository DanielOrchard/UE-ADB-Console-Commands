# UE ADB Console Commands

Simple Helper application for sending Unreal Engine console commands, over to a connected Android application via ADB. This was tested with a Meta Quest 3, but should work for any Android builds I believe. It is a PySide6 desktop app, featuring favourites, unreal-style autocomplete, and a history

Only wired ADB is supported, but im sure you could add wireless ADB easily.

## The List of commands
The app pulls from `ConsoleHelp.html` found in the root folder. This is the html doc that Unreal Engine can autogenerate, via help>console commands.  You can use the one included, or generate your own if you have custom console commands setup in source and want them in the autocomplete. Just generate your own then copy paste it over the origional. 


![UE ADB Console Commands window](docs/images/window.png)

**Highlights**
- Picks the connected headset automatically (manual refresh + status bar feedback)
- Double-click favourites or catalog rows to stage/send commands instantly
- Autocomplete + filter backed by Unreal's exported `ConsoleHelp.html`
- Built-in log so you can see every `adb` response without leaving the UI

## Requirements
- Windows with Python **3.10**; create a `.venv` in the repo root. Might work on other OS. Untested.
- ADB Installed and setup on PATH. 
- Edit `favourites.txt` to tune the quick-send list to whatever you frquently use. 

## Quick Start
Run `run.bat`

Alternatively: VS Code (recommended) Open root folder in VSCode, enable the `.venv` interpreter when prompted, and tick requirments.txt when it asks. It should pull all the resources needed. Then press `F5` or Run.

**Run Manually**
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python -m src.main
```


## Usage Notes
- The All Commands panel is collapsible; use the search box to filter by substring across command names and help.
- Double-clicking a row copies the command into the input so you can append arguments before sending.
- Logs stick around in the right pane—use them to confirm the broadcast succeeded or diagnose ADB issues.
- Dont forget you can run any Unreal Engine blueprint event via `ke [object] [event name]` if you dont care which object, use a asterix to run command on all. For example: `ke * Add1000Money` would run any event called "Add1000Money" that it could find anywhere. 
If the command is in the level blueprint, I think you swap `ke` for `ce`, and drop the [object] part, but im not certain so you should look this up. 