# WeChatNotifier

> A lightweight Windows notification enhancer for WeChat 4.x.  
> Windows 微信 4.x 系统通知增强工具。

WeChatNotifier monitors local WeChat session metadata and sends Windows Toast notifications for new messages. It is designed for users whose Windows WeChat client does not reliably show desktop notifications.

## Features

- Windows 10/11 Toast notifications
- Private chat notifications
- Normal group chat notifications
- Automatically ignores muted groups
- Automatically ignores Official Accounts / Service Accounts
- Automatically ignores WeChat internal placeholder/folded-session entries
- System tray icon
- Pause / resume notifications
- Test notification from the tray menu
- Local rotating log
- Single-instance protection
- Optional startup with Windows
- Standalone Windows executable can be distributed via GitHub Releases

## Tested environment

The current v1.0.0 logic was tested on:

- Windows 11 x64
- WeChat 4.1.13.12
- Python 3.12.14
- `wechatauto-replica` 1.1.10.2

Other WeChat 4.x versions may work, but they have not been fully validated.

## How it works

The program does **not** use the legacy Windows UI Automation route for message detection.

Instead, it reads local WeChat session/contact metadata through `wechatauto-replica`:

```text
WeChat
  ↓
local session/contact database
  ↓
detect unread-count changes
  ↓
filter muted groups / official accounts / internal sessions
  ↓
Windows Toast notification
```

The program only needs session/contact metadata for notification detection; it does not upload chat content to a remote server.

## Notification policy

| Message type | Notification |
|---|---|
| Private chat | Yes |
| Normal group chat | Yes |
| Muted group | No |
| Official Account | No |
| Service Account | No |
| `@placeholder_*` internal session | No |
| Existing unread messages at program startup | No |

For the tested WeChat 4.1.13.12 environment, muted-group status is derived from the local contact database (`chat_room_notify`), while Official/Service Account filtering additionally uses `verify_flag` and known internal session identifiers.

## Download

For most users, download the Windows executable from the **Releases** page:

**Releases → latest release → `WeChatNotifier.exe`**

The executable is built with PyInstaller.

> Windows SmartScreen or antivirus software may warn about an unsigned executable downloaded from the Internet. See the Security & privacy section below before running it.

## Run from source

### 1. Requirements

Recommended:

```text
Python 3.12 x64
Windows 10/11
WeChat logged in
```

Create an isolated environment if desired:

```powershell
conda create -n wechatnotify python=3.12 -y
conda activate wechatnotify
```

Install runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 2. Run

```powershell
python -u .\wechat_notify.py
```

The application will appear in the Windows system tray.

## Tray menu

Right-click the tray icon to access:

- Pause notifications
- Resume notifications
- Send test notification
- Open log
- Open log folder
- Enable/disable startup with Windows
- Exit

When notifications are resumed after a pause, WeChatNotifier rebuilds the unread-message baseline so that messages accumulated during the pause are not replayed as new notifications.

## Log

Logs are stored locally at:

```text
%LOCALAPPDATA%\WeChatNotifier\app.log
```

The log rotates automatically to avoid unlimited growth.

## Build Windows executable

Install build dependencies:

```powershell
python -m pip install -r requirements-build.txt
```

Build the final single-file background executable:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name WeChatNotifier --hidden-import=pystray._win32 .\wechat_notify.py
```

If `pystray` backend collection fails on your machine, use:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name WeChatNotifier --collect-all pystray .\wechat_notify.py
```

The executable will be created under:

```text
dist\WeChatNotifier.exe
```

## Release checksum

Before publishing a release, calculate SHA-256:

```powershell
Get-FileHash .\dist\WeChatNotifier.exe -Algorithm SHA256
```

Copy the hash into the GitHub Release notes so users can verify the downloaded executable.

## Security & privacy

WeChatNotifier is an unofficial local utility.

- It does not provide a cloud backend.
- It does not intentionally upload message content.
- It depends on `wechatauto-replica` to access locally stored WeChat data.
- That upstream library may perform local read-only process-memory access to obtain information required to read encrypted WeChat databases.
- Because the executable is unsigned and uses PyInstaller, Windows SmartScreen or heuristic antivirus engines may show warnings.

Users who prefer maximum transparency should review the source and run it directly with Python.

## Compatibility notes

The implementation relies on internal data structures of the Windows WeChat client. Tencent may change these structures in future releases.

If notifications stop working after a WeChat update:

1. Open the tray menu → **Open log**.
2. Check whether the WeChat database can still be opened.
3. Verify whether muted-group and Official Account fields are still detected.
4. Check for a newer compatible `wechatauto-replica` release.
5. Open a GitHub Issue and include the WeChat version and relevant sanitized log lines.

Do **not** post private chat content, account identifiers, database keys, or other sensitive information in public issues.

## Disclaimer

This is an unofficial project and is not affiliated with, endorsed by, or sponsored by Tencent or WeChat.

This project is intended for personal productivity, learning, and local automation. Users are responsible for complying with applicable laws, organizational policies, and the WeChat software license agreement.

## License

WeChatNotifier source code is released under the MIT License.

Third-party dependencies use their own licenses. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
