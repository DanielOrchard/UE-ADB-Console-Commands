"""PySide6 UI for sending Unreal console commands via ADB.

Entry point for the desktop application. Uses adbutils via `adb_client`
for device communication and parses Unreal's `ConsoleHelp.html` via
`commands_loader` to power autocomplete.
"""
from __future__ import annotations

import configparser
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .adb_client import (
    ensure_adb_available,
    get_default_device,
    list_devices,
    send_unreal_command,
)
from .commands_loader import UnrealCommand, load_commands

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FAVOURITES_FILE = PROJECT_ROOT / "favourites.ini"
HISTORY_FILE = PROJECT_ROOT / "history.ini"
MAX_HISTORY = 50
DEFAULT_FAVOURITES = [
    "stat unit",
    "stat fps",
    "r.MSAACount 4",
    "r.MSAACount 8",
    "r.Antiailising 3",
]


def load_favourite_commands(path: Path = FAVOURITES_FILE) -> list[str]:
    """Load favourite commands from INI file."""
    config = configparser.ConfigParser()
    try:
        config.read(path, encoding="utf-8")
        if "Commands" in config:
            # INI stores as key=value; we use the value part
            favourites = [cmd for cmd in config["Commands"].values() if cmd.strip()]
            return favourites if favourites else DEFAULT_FAVOURITES.copy()
    except Exception:
        pass
    return DEFAULT_FAVOURITES.copy()


def load_history_commands(path: Path = HISTORY_FILE) -> list[str]:
    """Load command history from INI file (most-recent first)."""
    config = configparser.ConfigParser()
    try:
        config.read(path, encoding="utf-8")
        if "History" in config:
            return [cmd for cmd in config["History"].values() if cmd.strip()]
    except Exception:
        pass
    return []


def save_history_commands(commands: list[str], path: Path = HISTORY_FILE) -> bool:
    """Persist command history to INI file."""
    config = configparser.ConfigParser()
    config["History"] = {}
    for idx, cmd in enumerate(commands, start=1):
        config["History"][f"cmd{idx}"] = cmd
    try:
        with path.open("w", encoding="utf-8") as f:
            config.write(f)
        return True
    except Exception:
        return False


def add_history_command(command: str, path: Path = HISTORY_FILE) -> bool:
    """Insert command into history (most-recent first) and persist."""
    if not command.strip():
        return False
    history = load_history_commands(path)
    history = [cmd for cmd in history if cmd != command]
    history.insert(0, command)
    history = history[:MAX_HISTORY]
    return save_history_commands(history, path)


def save_favourite_command(command: str, path: Path = FAVOURITES_FILE) -> bool:
    """Save a command to favourites INI file. Returns True if successful."""
    if not command.strip():
        return False
    
    config = configparser.ConfigParser()
    
    # Load existing favourites
    try:
        config.read(path, encoding="utf-8")
    except Exception:
        pass
    
    # Ensure Commands section exists
    if "Commands" not in config:
        config["Commands"] = {}
    
    # Check if command already exists
    existing_commands = [cmd for cmd in config["Commands"].values()]
    if command in existing_commands:
        return False  # Already exists
    
    # Add new command with a numbered key
    key_num = len(config["Commands"]) + 1
    config["Commands"][f"cmd{key_num}"] = command
    
    # Write back to file
    try:
        with path.open("w", encoding="utf-8") as f:
            config.write(f)
        return True
    except Exception:
        return False


def delete_favourite_command(command: str, path: Path = FAVOURITES_FILE) -> bool:
    """Delete a command from favourites INI file. Returns True if successful."""
    if not command.strip():
        return False
    
    config = configparser.ConfigParser()
    
    # Load existing favourites
    try:
        config.read(path, encoding="utf-8")
    except Exception:
        return False
    
    if "Commands" not in config:
        return False
    
    # Find and remove the command
    key_to_delete = None
    for key, value in config["Commands"].items():
        if value == command:
            key_to_delete = key
            break
    
    if key_to_delete:
        del config["Commands"][key_to_delete]
        
        # Write back to file
        try:
            with path.open("w", encoding="utf-8") as f:
                config.write(f)
            return True
        except Exception:
            return False
    
    return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unreal Engine ADB Console Commands")
        self.resize(820, 560)

        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)

        # Device selection row
        device_row = QHBoxLayout()
        self.device_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Devices")
        self.refresh_button.clicked.connect(self.refresh_devices)
        device_row.addWidget(QLabel("Device:"))
        device_row.addWidget(self.device_combo)
        device_row.addWidget(self.refresh_button)
        root_layout.addLayout(device_row)

        # Load favourites from text file
        self.favourite_commands: list[str] = load_favourite_commands()
        self.history_commands: list[str] = load_history_commands()

        # Load full command catalog from HTML; fall back to favourites if missing
        self.full_commands: list[UnrealCommand] = load_commands()
        self.full_catalog_available = bool(self.full_commands)
        if not self.full_commands:
            self.full_commands = [
                UnrealCommand(name=cmd, help="", type="")
                for cmd in self.favourite_commands
            ]
        self.full_command_names = [c.name for c in self.full_commands]

        # Command input row + autocomplete
        cmd_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Type Unreal command; autocomplete active")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_manual_command)
        self.command_input.returnPressed.connect(self.send_manual_command)
        self.save_fav_button = QPushButton("Save to Favourites")
        self.save_fav_button.clicked.connect(self.save_current_to_favourites)
        cmd_row.addWidget(QLabel("Command:"))
        cmd_row.addWidget(self.command_input, 4)
        cmd_row.addWidget(self.send_button)
        cmd_row.addWidget(self.save_fav_button)
        root_layout.addLayout(cmd_row)

        self.completer = QCompleter(self.full_command_names)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.command_input.setCompleter(self.completer)

        # Favourites + History lists
        lists_row = QHBoxLayout()

        fav_col = QVBoxLayout()
        self.fav_list = QListWidget()
        self.fav_list.itemDoubleClicked.connect(self.send_selected_favorite)
        self.fav_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fav_list.customContextMenuRequested.connect(self.show_favourites_context_menu)
        fav_col.addWidget(QLabel("Favourites:"))
        fav_col.addWidget(self.fav_list, 1)

        hist_col = QVBoxLayout()
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.send_selected_history)
        hist_col.addWidget(QLabel("History:"))
        hist_col.addWidget(self.history_list, 1)

        lists_row.addLayout(fav_col, 1)
        lists_row.addLayout(hist_col, 1)
        root_layout.addLayout(lists_row, 3)

        # Collapsible full list panel
        self.full_toggle = QToolButton(text="Show All Commands")
        self.full_toggle.setCheckable(True)
        self.full_toggle.setChecked(False)
        self.full_toggle.setArrowType(Qt.RightArrow)
        self.full_toggle.clicked.connect(self.toggle_full_panel)
        toggle_row = QHBoxLayout()
        toggle_row.addWidget(self.full_toggle)
        toggle_row.addWidget(QLabel("(double-click to send)"))
        toggle_row.addStretch()
        root_layout.addLayout(toggle_row)

        self.full_panel = QWidget()
        self.full_panel.setVisible(False)
        full_layout = QVBoxLayout(self.full_panel)
        filter_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter (substring, case-insensitive)")
        self.filter_input.textChanged.connect(self.filter_full_list)
        self.reset_filter_btn = QPushButton("Clear")
        self.reset_filter_btn.clicked.connect(lambda: self.filter_input.clear())
        filter_row.addWidget(QLabel("Search:"))
        filter_row.addWidget(self.filter_input, 4)
        filter_row.addWidget(self.reset_filter_btn)
        full_layout.addLayout(filter_row)
        self.full_table = QTableWidget()
        self.full_table.setColumnCount(2)
        self.full_table.setHorizontalHeaderLabels(["Command", "Help"])
        header = self.full_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.full_table.verticalHeader().setVisible(False)
        self.full_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.full_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.full_table.setSelectionMode(QTableWidget.SingleSelection)
        self.full_table.cellDoubleClicked.connect(self.send_selected_full)
        full_layout.addWidget(self.full_table, 4)
        root_layout.addWidget(self.full_panel, 3)

        # Log output
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        root_layout.addWidget(QLabel("Log:"))
        root_layout.addWidget(self.log, 1)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Initializing...")

        self.populate_favourites()
        self.populate_history()
        self.populate_full_list()
        self.refresh_devices()

        if not self.full_catalog_available:
            self.append_log("ConsoleHelp.html not found or unreadable; using favourites list for autocomplete.")
        else:
            self.append_log(f"Loaded {len(self.full_command_names)} commands from ConsoleHelp.html.")

        # Periodic auto-refresh (optional) every 15s to catch new devices
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_devices)
        self.auto_refresh_timer.start(15000)

        ok, msg = ensure_adb_available()
        self.append_log(msg)
        if not ok:
            self.status_bar.showMessage("ADB issue: " + msg)
        else:
            self.status_bar.showMessage(msg)

    # -------- Utility methods --------
    def append_log(self, text: str):
        self.log.append(text)

    def current_device(self):  # returns adbutils device or None
        idx = self.device_combo.currentIndex()
        if idx < 0:
            return None
        serial = self.device_combo.currentData()
        if not serial:
            return None
        # Retrieve the matching device from list
        for dev in list_devices():
            if dev.serial == serial:
                return dev
        return None

    def populate_favourites(self):
        self.fav_list.clear()
        for cmd in self.favourite_commands:
            QListWidgetItem(cmd, self.fav_list)

    def populate_history(self):
        self.history_list.clear()
        for cmd in self.history_commands:
            QListWidgetItem(cmd, self.history_list)

    def populate_full_list(self, commands: Optional[list[UnrealCommand]] = None):
        data = commands if commands is not None else self.full_commands
        self.filtered_commands = data
        self.full_table.setRowCount(len(data))
        for row, cmd in enumerate(data):
            command_item = QTableWidgetItem(cmd.name)
            help_item = QTableWidgetItem(cmd.help)
            command_item.setFlags(command_item.flags() & ~Qt.ItemIsEditable)
            help_item.setFlags(help_item.flags() & ~Qt.ItemIsEditable)
            self.full_table.setItem(row, 0, command_item)
            self.full_table.setItem(row, 1, help_item)

    def toggle_full_panel(self, checked: bool):
        self.full_panel.setVisible(checked)
        self.full_toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.full_toggle.setText("Hide All Commands" if checked else "Show All Commands")

    def filter_full_list(self):
        term = self.filter_input.text().strip().lower()
        if not term:
            filtered = self.full_commands
        else:
            filtered = [
                cmd
                for cmd in self.full_commands
                if term in cmd.name.lower() or term in cmd.help.lower()
            ]
        self.populate_full_list(filtered)

    # -------- ADB / devices --------
    def refresh_devices(self):
        devices = list_devices()
        selected_serial = self.device_combo.currentData()
        self.device_combo.clear()
        for dev in devices:
            self.device_combo.addItem(dev.serial, dev.serial)
        if devices:
            self.status_bar.showMessage(f"{len(devices)} device(s) available.")
            # Restore previous selection if possible
            if selected_serial:
                idx = self.device_combo.findData(selected_serial)
                if idx >= 0:
                    self.device_combo.setCurrentIndex(idx)
        else:
            self.status_bar.showMessage("No devices connected.")

    # -------- Sending commands --------
    def _send_command(self, cmd: str):
        if not cmd.strip():
            return
        dev = self.current_device() or get_default_device()
        self.append_log(f"Sending: {cmd}")
        ok, msg = send_unreal_command(cmd, dev)
        if add_history_command(cmd):
            self.history_commands = load_history_commands()
            self.populate_history()
        if ok:
            self.append_log(f"OK: {msg}")
            self.status_bar.showMessage(f"Sent '{cmd}'")
        else:
            self.append_log(f"ERROR: {msg}")
            self.status_bar.showMessage(f"Failed '{cmd}'")

    def send_manual_command(self):
        cmd = self.command_input.text()
        self._send_command(cmd)

    def send_selected_favorite(self, item: QListWidgetItem):
        self._send_command(item.text())

    def send_selected_history(self, item: QListWidgetItem):
        self._send_command(item.text())

    def send_selected_full(self, row: int, column: int):  # noqa: ARG002
        if row < 0:
            return
        command_item = self.full_table.item(row, 0)
        if not command_item:
            return
        command = command_item.text()
        self.command_input.setText(command)
        self.command_input.setFocus()
        self.status_bar.showMessage(f"Prepared '{command}' — edit arguments and press Send")

    def save_current_to_favourites(self):
        """Save the current command in the input field to favourites."""
        cmd = self.command_input.text().strip()
        if not cmd:
            self.status_bar.showMessage("No command to save")
            return
        
        if save_favourite_command(cmd):
            self.favourite_commands = load_favourite_commands()
            self.populate_favourites()
            self.append_log(f"Saved to favourites: {cmd}")
            self.status_bar.showMessage(f"Saved '{cmd}' to favourites")
        else:
            self.status_bar.showMessage(f"'{cmd}' already in favourites")
            self.append_log(f"Command already in favourites: {cmd}")

    def show_favourites_context_menu(self, position):
        """Show context menu for favourites list."""
        item = self.fav_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        send_action = menu.addAction("Send Command")
        copy_action = menu.addAction("Copy to Command Box")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Favourite")
        
        action = menu.exec(self.fav_list.mapToGlobal(position))
        
        if action == send_action:
            self._send_command(item.text())
        elif action == copy_action:
            self.command_input.setText(item.text())
            self.command_input.setFocus()
            self.status_bar.showMessage(f"Copied '{item.text()}' to command box")
        elif action == delete_action:
            self.delete_favourite(item.text())
    
    def delete_favourite(self, command: str):
        """Delete a favourite command."""
        if delete_favourite_command(command):
            self.favourite_commands = load_favourite_commands()
            self.populate_favourites()
            self.append_log(f"Deleted from favourites: {command}")
            self.status_bar.showMessage(f"Deleted '{command}' from favourites")
        else:
            self.status_bar.showMessage(f"Failed to delete '{command}'")
            self.append_log(f"Failed to delete: {command}")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
