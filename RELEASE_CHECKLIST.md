# v1.0.0 Release Checklist

Use this checklist before pressing **Publish release** on GitHub.

## Repository

- [ ] `wechat_notify.py` uploaded
- [ ] `README.md` updated
- [ ] `requirements.txt` uploaded
- [ ] `requirements-build.txt` uploaded
- [ ] `THIRD_PARTY_NOTICES.md` uploaded
- [ ] `LICENSE` present
- [ ] `.gitignore` present
- [ ] No logs, database files, keys, local paths, wxids, screenshots containing private chats, or personal data committed

## Source verification

- [ ] Source starts successfully on Python 3.12
- [ ] Tray icon works
- [ ] Pause/resume works
- [ ] Test notification works
- [ ] Log opens
- [ ] Single-instance protection works
- [ ] Startup toggle works

## Notification regression test

- [ ] Private chat → notification
- [ ] Normal group → notification
- [ ] Muted group → ignored
- [ ] Official Account → ignored
- [ ] Service Account → ignored
- [ ] `@placeholder_*` → ignored
- [ ] Historical unread messages are not replayed at startup

## Binary

- [ ] Built with final command
- [ ] `--onefile --noconsole` tested
- [ ] `WeChatNotifier.exe` moved to a clean release folder
- [ ] EXE launches with no console window
- [ ] EXE appears in system tray
- [ ] Second launch does not create a second active instance
- [ ] EXE exits cleanly from tray menu

## Build command

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name WeChatNotifier --hidden-import=pystray._win32 .\wechat_notify.py
```

Fallback:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name WeChatNotifier --collect-all pystray .\wechat_notify.py
```

## Hash

Run:

```powershell
Get-FileHash .\WeChatNotifier.exe -Algorithm SHA256
```

- [ ] SHA-256 copied into release description

## GitHub Release

- [ ] Tag: `v1.0.0`
- [ ] Title: `WeChatNotifier v1.0.0`
- [ ] `WeChatNotifier.exe` attached under Assets
- [ ] Release notes copied from `RELEASE_NOTES_v1.0.0.md`
- [ ] SmartScreen/unsigned-executable notice included
- [ ] Tested WeChat version stated explicitly
- [ ] Release published
