# UE ADB Console Commands

PySide6 desktop app for firing Unreal Engine console commands to an Android headset over ADB—favourites, autocomplete, and a full catalog powered by `ConsoleHelp.html`.

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
VS Code (recommended) Open root folder in VSCode, enable the `.venv` interpreter when prompted, and tick requirments.txt when it asks. It should pull all the resources needed. Then press `F5` or Run.

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
