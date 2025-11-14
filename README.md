# UE ADB Console Commands

PySide6 desktop app for firing Unreal Engine console commands to an Android headset over ADB—favourites, autocomplete, and a full catalog powered by `ConsoleHelp.html`.

![UE ADB Console Commands window](docs/images/window.png)

**Highlights**
- Picks the connected headset automatically (manual refresh + status bar feedback)
- Double-click favourites or catalog rows to stage/send commands instantly
- Autocomplete + filter backed by Unreal's exported `ConsoleHelp.html`
- Built-in log so you can see every `adb` response without leaving the UI

## Requirements
- Windows with Python **3.10**; create a `.venv` in the repo root.
- Android Platform Tools on PATH and an authorized Unreal headset listening for `android.intent.action.RUN` with string extra `cmd`.
- Optional but recommended: drop the latest `ConsoleHelp.html` export into the repo root (UE ➜ Help ➜ Console Variables) so autocomplete and the All Commands table stay in sync with your project.
- Edit `favourites.txt` to tune the quick-send list.

## Quick Start
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

1. Copy your freshly exported `ConsoleHelp.html` next to `README.md` (optional fallback to favourites if omitted).
2. Launch from VS Code (recommended): open the folder, pick the `.venv` interpreter when prompted, then press `F5` (or use Run and Debug → **Run Unreal Commands UI**).
3. Prefer a terminal? With the venv active run `python -m src.main`.

## Usage Notes
- The All Commands panel is collapsible; use the search box to filter by substring across command names and help.
- Double-clicking a row copies the command into the input so you can append arguments before sending.
- Logs stick around in the right pane—use them to confirm the broadcast succeeded or diagnose ADB issues.
