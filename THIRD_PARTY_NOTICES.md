# Third-Party Notices

WeChatNotifier depends on third-party open-source software. Each dependency remains subject to its own license.

This file is a project-level notice and is **not a substitute for the complete upstream license texts**. When distributing a bundled executable, retain the applicable notices/licenses required by each dependency.

## Runtime dependencies

### wechatauto-replica

- Purpose: access to local WeChat data / automation support
- Tested version: `1.1.10.2`
- License: Apache License 2.0
- Upstream project: `fanyuantaier/wechatauto-replica`

Important: this dependency may access the local WeChat process and encrypted local databases. Review the upstream documentation before use or redistribution.

### win11toast

- Purpose: Windows 10/11 Toast notifications
- Tested version: `0.36.3`
- License: MIT License
- Upstream project: `GitHub30/win11toast`

### pystray

- Purpose: Windows system-tray integration
- Tested version: `0.19.5`
- License: GNU Lesser General Public License v3 (LGPLv3)
- Upstream project: `moses-palmer/pystray`

Because binary releases may bundle this library, distributors should review the LGPL obligations applicable to their distribution method.

### Pillow

- Purpose: generation of the tray icon image
- Tested version: `12.3.0`
- License: MIT-CMU / HPND-style Pillow license
- Upstream project: `python-pillow/Pillow`

## Build dependency

### PyInstaller

- Purpose: building the standalone Windows executable
- Tested/recommended version: `6.22.2`
- License: GPL-2.0-or-later with the PyInstaller bootloader exception permitting distribution of bundled applications under additional conditions
- Upstream project: `pyinstaller/pyinstaller`

PyInstaller is a build-time dependency and is not part of WeChatNotifier's source-code license.

## Notes for binary releases

For GitHub Release binaries:

1. Keep this notice with the source repository.
2. Preserve the project's own `LICENSE`.
3. Review and preserve third-party license notices as required.
4. Publish the source revision/tag used to build each binary.
5. Publish a SHA-256 checksum for each executable.
6. Do not imply that Tencent/WeChat endorses this project.

This document is provided for practical project organization and is not legal advice.
