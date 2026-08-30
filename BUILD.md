# Build Guide

## Recommended build environment

- Windows 11 x64
- Python 3.12 x64
- Conda environment name: `wechatnotify` (optional)

## 1. Create environment

```powershell
conda create -n wechatnotify python=3.12 -y
conda activate wechatnotify
```

## 2. Install dependencies

```powershell
python -m pip install -r requirements-build.txt
```

## 3. Test source

```powershell
python -u .\wechat_notify.py
```

Verify tray controls and message filtering before packaging.

## 4. Build final EXE

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name WeChatNotifier --hidden-import=pystray._win32 .\wechat_notify.py
```

Fallback if `pystray` is not collected correctly:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name WeChatNotifier --collect-all pystray .\wechat_notify.py
```

Output:

```text
dist\WeChatNotifier.exe
```

## 5. Test packaged EXE

Test all of the following:

- private chat notification
- normal group notification
- muted group ignored
- Official/Service Account ignored
- placeholder/folded session ignored
- tray menu
- pause/resume
- test notification
- log access
- startup toggle
- single-instance protection
- clean tray exit

## 6. Compute SHA-256

```powershell
Get-FileHash .\dist\WeChatNotifier.exe -Algorithm SHA256
```

Copy the hash into the release notes.

## 7. Publish

Create GitHub tag/release:

```text
v1.0.0
```

Attach only the final `WeChatNotifier.exe` to the Release Assets section. Keep build outputs out of the normal Git repository.
