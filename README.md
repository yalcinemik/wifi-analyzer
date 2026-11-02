# Wifi Analyzer
A live Wi-Fi network analyzer for Windows. It lists all nearby Wi-Fi networks
sorted by signal strength and shows them together on a single spectrum screen,
so you can see at a glance which networks are strong and which are weak.

## Features

- Live scanning with networks sorted by signal strength
- Color-coded signal bars for every network on one screen
- Click any network to see its channel, MAC address and proximity info
- Turkish / English language menu (switches instantly)
- Save scan results as a .txt log file

## Usage

Requires Python 3 on Windows. No extra packages needed.

    python wifi_scanner.py

## Notes

- The Wi-Fi adapter must be turned on.
- On recent Windows versions, location services must be enabled, otherwise
  the scan may return no results.
- Works on Windows only (uses the built-in `netsh` command).

## Build an .exe

    pip install pyinstaller
    pyinstaller --onefile --noconsole wifi_scanner.py
