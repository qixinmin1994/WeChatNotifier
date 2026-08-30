# WeChatNotifier v1.0.0

Initial public release.

## Highlights

- Windows Toast notifications for incoming WeChat messages
- Private-chat notification support
- Normal group-chat notification support
- Automatic filtering of muted groups
- Automatic filtering of Official Accounts / Service Accounts
- Filtering of WeChat internal placeholder/folded-session entries
- System-tray operation
- Pause/resume controls
- Test notification
- Local rotating logs
- Single-instance protection
- Optional startup with Windows
- Standalone `--onefile --noconsole` Windows build

## Tested environment

- Windows 11 x64
- WeChat 4.1.13.12
- Python 3.12.14
- `wechatauto-replica` 1.1.10.2

## Installation

For most users, download:

```text
WeChatNotifier.exe
```

from the Assets section of this release and run it.

The application runs in the Windows system tray.

## Important notes

This is an unofficial utility and is not affiliated with Tencent or WeChat.

The executable is unsigned. Windows SmartScreen or antivirus software may display a warning for an Internet-downloaded PyInstaller executable.

The program uses local WeChat data through `wechatauto-replica`; no cloud backend is provided by WeChatNotifier.

## SHA-256

Before publishing, replace the placeholder below with the output of:

```powershell
Get-FileHash .\WeChatNotifier.exe -Algorithm SHA256
```

```text
WeChatNotifier.exe
SHA256: REPLACE_WITH_ACTUAL_SHA256
```

## Known limitations

- Compatibility is validated on WeChat 4.1.13.12, not every WeChat 4.x build.
- Internal WeChat database fields may change in future versions.
- Notification sender identity/display may vary with Windows Toast behavior.
- The application is currently Windows-only.

## Upgrade notes

Before upgrading WeChat, keep a copy of the currently working WeChatNotifier release. If a WeChat update breaks message detection, check the local log and open an Issue with sanitized diagnostics.
