# BitStar Windows Installer Plan

This document defines the first BitStar Windows installer path. It is an
intermediate release-engineering step between a zip package and a fully signed
production installer.

## Installer Type

Initial installer technology: NSIS.

Reason:

- Bitcoin Core already carries NSIS packaging support.
- NSIS can build a simple user-mode installer from the existing BitStar Windows
  package.
- It can create Start Menu shortcuts and an uninstaller without requiring an
  MSI toolchain.

## Installer Scope

The first BitStar installer should install only application files:

- `bitstar.exe`
- `bitstard.exe`
- `bitstar-cli.exe`
- `bitstar-util.exe`
- `sqlite3.dll`
- launcher `.bat` and `.ps1` files
- README and release notes, when present

The installer must not install, modify, or delete:

- wallet files;
- chainstate or block data;
- `%LOCALAPPDATA%\BitStar`;
- `bitstar.conf`, except when the user launches the BitStar launcher and the
  launcher creates or updates it.

## Install Location

Default install location:

```text
%LOCALAPPDATA%\Programs\BitStar Core
```

This avoids requiring administrator rights for early release-candidate testing.
A future production installer may offer a machine-wide install path after code
signing and upgrade behavior are fully tested.

## Shortcuts

The installer should create Start Menu shortcuts:

- `BitStar Launcher`
- `BitStar GUI`
- `BitStar Console`
- `Uninstall BitStar Core`

The default user-facing entry point should be `BitStar Launcher`, not the raw
daemon.

## Build Command

After creating or extracting a Windows package folder, validate it first:

```powershell
powershell -ExecutionPolicy Bypass -File .\contrib\bitstar\release\build-windows-installer.ps1 `
  -PackageDir "C:\path\to\BitStar_Windows_v0.1.2-rc2" `
  -Version "v0.1.2-rc2" `
  -CheckOnly
```

Build the installer when NSIS is installed:

```powershell
powershell -ExecutionPolicy Bypass -File .\contrib\bitstar\release\build-windows-installer.ps1 `
  -PackageDir "C:\path\to\BitStar_Windows_v0.1.2-rc2" `
  -Version "v0.1.2-rc2" `
  -OutputDir "C:\path\to\outputs"
```

Expected output:

```text
BitStar_Core_Setup_v0.1.2-rc2.exe
```

## Current Test Artifact

The `v0.1.2-rc2` installer was built with NSIS 3.12 from the verified Windows
zip package and published as unsigned pre-release software.

```text
Artifact: BitStar_Core_Setup_v0.1.2-rc2.exe
SHA256: b1a8d3aea370beb6126daf37e70902e53cef29ec0e7778cdfd89c033d94330ad
Signed manifest: SHA256SUMS-v0.1.2-rc2
Smoke test: silent install/uninstall to a temporary user directory passed
Production status: not production-ready; code signing and independent repeat pending
```

## Release Rules

The installer should not be published as production until:

- installer artifact has SHA256 checksum;
- checksum is included in the signed release manifest;
- installer installs successfully on a clean Windows user profile;
- launcher starts and stops the node from the installed path;
- wallet backup action is smoke-tested;
- uninstall leaves `%LOCALAPPDATA%\BitStar` intact;
- upgrade over a previous installer is tested;
- Windows Authenticode signing is available, or the release notes clearly label
  the installer as unsigned pre-release software.

## Future Improvements

- Add Authenticode signing.
- Add a native GUI launcher or tray launcher.
- Add installer option to start BitStar after install.
- Add installer option to open the verification guide.
- Add automatic pre-upgrade node shutdown warning.
- Add a reproducible installer build path.
