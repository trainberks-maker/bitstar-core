# BitStar Launcher Production Checklist

This checklist tracks the work required before the Windows launcher can be
treated as a production-ready user entry point.

Current launcher status: release-candidate helper launcher.

Current target package: `BitStar_Windows_v0.1.2-rc3.zip`

Installer plan: [windows-installer-plan.md](windows-installer-plan.md)

## Current Capabilities

The Windows launcher package currently includes:

- `BitStar-Launcher.bat`
- `BitStar-Launcher.ps1`
- `Start-BitStar-Node.bat`
- `Check-BitStar-Status.bat`
- `Stop-BitStar-Node.bat`
- `Open-BitStar-Console.bat`
- `Show-BitStar-Wallet-Address.bat`
- `bitstard.exe`
- `bitstar-cli.exe`
- `bitstar-util.exe`
- `bitstar.exe`
- `sqlite3.dll`

The current package does not include `bitstar-qt.exe`, so it is treated as a
node and CLI wallet package. GUI wallet shortcuts are only created when a
package includes `bitstar-qt.exe`.

The launcher can:

- create `%LOCALAPPDATA%\BitStar\bitstar.conf`;
- keep RPC bound to `127.0.0.1`;
- generate a local RPC password;
- add `seed1.bitstarcoin.org:21333`;
- add `seed2.bitstarcoin.org:21333`;
- start `bitstard.exe`;
- show block height, best block, IBD state, and peer count;
- create or load `wallet1`;
- print a Bech32 `bst1...` receiving address for mining;
- print a cpuminer command for `pool.bitstarcoin.org:3333`;
- open the GUI only when `bitstar-qt.exe` is present;
- back up loaded wallets;
- open the data directory;
- stop the node cleanly.

## Production Gates

### Gate 1: Package Integrity

Definition of done:

- Windows package has a SHA256 checksum.
- Package is included in the signed `SHA256SUMS-*` manifest.
- `scan-release-package.ps1` passes.
- No wallet files, chain data, RPC credentials, SSH keys, or API tokens are
  included.
- A clean extraction smoke test passes.

Current status: passed for `v0.1.2-rc3`. The package is included in the signed
`SHA256SUMS-v0.1.2-rc3` manifest, and external Windows verification report #1
passed for the release candidate. Optional additional outside repeats remain
welcome before final production promotion.

### Gate 2: Installer

Definition of done:

- A Windows installer is built from the verified Windows package.
- Installer installs into a user-writable app directory.
- Installer creates Start Menu shortcuts for:
  - BitStar Launcher;
  - Show BitStar Wallet Address;
  - BitStar GUI, only when the package includes `bitstar-qt.exe`;
  - BitStar Console;
  - Uninstall.
- Installer does not delete `%LOCALAPPDATA%\BitStar` on uninstall.
- Installer can upgrade over the previous installer without deleting user data.
- Installer artifact has SHA256 checksum and is included in the signed manifest.

Current status: installer scaffold exists; `BitStar_Core_Setup_v0.1.2-rc3.exe`
was built, smoke-tested, included in the signed manifest, published as
unsigned pre-release software, and passed the internal Windows installer
production gate.

Gate record:
[windows-installer-production-gate-v0.1.2-rc3.md](windows-installer-production-gate-v0.1.2-rc3.md)

Manual promotion repeat:
[windows-installer-production-promotion-v0.1.2-rc3.md](windows-installer-production-promotion-v0.1.2-rc3.md)

It is not a final production installer yet because Authenticode signing,
dedicated independent installer repeat testing, previous-installer upgrade
testing, and a real GUI build including `bitstar-qt.exe` are still pending.

Build helper:
`contrib/bitstar/release/build-windows-installer.ps1`

### Gate 3: Code Signing

Definition of done:

- `bitstar.exe`, `bitstard.exe`, `bitstar-cli.exe`, launcher scripts or
  launcher wrapper, and installer are signed where applicable.
- Signature publisher name is documented.
- Verification command is documented.
- Unsigned packages are clearly labeled as unsigned pre-release packages.

Current status: Windows Authenticode signing is pending.

### Gate 4: User Safety

Definition of done:

- Launcher never exposes RPC on a public interface.
- Launcher warns before wallet backup failure.
- Launcher gives clear errors when `bitstard.exe`, `bitstar-cli.exe`, or
  `sqlite3.dll` are missing.
- Launcher can recover gracefully if the node is still starting.
- Launcher can stop the node cleanly before upgrade.
- Installer does not overwrite wallet data.

Current status: partially complete.

### Gate 5: Upgrade Testing

Definition of done:

- Fresh install test passes on a clean Windows profile.
- Upgrade from the previous BitStar Windows package passes.
- Upgrade from the previous BitStar installer passes once installer artifacts
  exist.
- Existing `%LOCALAPPDATA%\BitStar` data directory remains intact.
- Existing wallet remains untouched unless the user explicitly backs it up.
- Node starts after upgrade and reports the expected genesis hash.

Current status: zip-package upgrade smoke test passed internally for
`v0.1.1-bootstrap` to `v0.1.2-rc2`; installer silent install/uninstall,
launcher start/stop, wallet backup, and data-preserving uninstall gate passed
internally for `v0.1.2-rc3`; external Windows verification report #1 passed for
`v0.1.2-rc3`; previous-installer upgrade and dedicated independent installer
repeat remain pending.

### Gate 6: Public Website

Definition of done:

- Download page labels the build as release candidate or production.
- Download page links:
  - installer;
  - zip package;
  - SHA256 manifest;
  - GPG signature;
  - public release key;
  - verification guide.
- Website warns when Windows code signing is not yet available.

Current status: GitHub release includes the installer artifact, and the website
links the installer, zip package, signed checksum manifest, public release key,
and verification guide while labeling Windows builds as unsigned pre-release
software.

## Required Release Record

Before a launcher build is promoted, record:

```text
BitStar launcher release record

Release tag:
Windows package:
Windows package SHA256:
Installer:
Installer SHA256:
Signed manifest:
Package scan result:
Clean install test:
Upgrade test:
Wallet backup test:
Uninstall leaves data directory intact:
Code signing status:
Independent verification issue:
Result: PASS/FAIL
Notes:
```

## Current Recommendation

Keep `v0.1.2-rc3` labeled as a signed release candidate. The next practical
launcher step is the Windows installer production promotion repeat: a
clean-profile Windows install from the published installer, Start Menu launch,
node start/stop, wallet address generation, wallet backup, uninstall, and
confirmation that `%LOCALAPPDATA%\BitStar` is preserved. After that, complete
previous-installer upgrade testing and Authenticode signing before the installer
is treated as production-ready.
