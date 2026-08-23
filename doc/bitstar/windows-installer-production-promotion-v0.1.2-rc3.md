# BitStar Windows Installer Production Promotion Repeat - v0.1.2-rc3

This is the manual repeat required before the Windows installer can be promoted
from unsigned pre-release testing toward production-ready launcher status.

Current decision: **HOLD**

The internal installer gate passed, and external Windows verification report #1
passed for the release candidate. This promotion repeat is still required
because normal Windows users should be able to install, launch, back up, stop,
and uninstall BitStar without using developer commands.

## 2026-08-23 Portable Launcher Repeat Finding

A repeat against the Windows portable `v0.1.2-rc3` package found that launcher
status, data-folder open, wallet backup, GUI warning, and node stop all behaved
as expected, but option `3` did not handle an existing unloaded `wallet1`
gracefully.

Observed failure:

```text
Wallet file verification failed. Failed to create database path
'...\BitStar\wallets\wallet1'. Database already exists.
WARNING: Could not load or create wallet 'wallet1'.
```

Root cause:

- the launcher attempted `createwallet wallet1` after `loadwallet wallet1`
  failed;
- when the wallet directory already existed, `createwallet` correctly refused
  to overwrite it;
- the launcher did not retry the safe existing-wallet path or save the printed
  mining address for normal users.

Source fix:

- load `wallet1` when it already exists;
- create `wallet1` only when it is absent;
- never overwrite an existing wallet directory;
- save the generated mining address to `Desktop\bitstar-address.txt`;
- make wallet backup load the default wallet if no wallet is already loaded.

Gate impact:

- the published `v0.1.2-rc3` artifacts remain pre-fix;
- production promotion remains **HOLD**;
- the next Windows package or installer candidate must include this launcher
  fix and repeat the checks below.

## Scope

Use a clean Windows profile, Windows Sandbox, or a disposable Windows VM.

Do not use:

- a real wallet with funds;
- a developer data directory;
- private keys, wallet seeds, SSH keys, RPC passwords, or API tokens;
- an existing production node data directory.

## Artifacts

- Release tag: `v0.1.2-rc3`
- Installer: `BitStar_Core_Setup_v0.1.2-rc3.exe`
- Installer SHA256:
  `954ed1bb71c51daef237cd0de8cf293165d38c74d0fff24e8861b5c1c343ce42`
- Signed manifest: `SHA256SUMS-v0.1.2-rc3`
- Manifest signature: `SHA256SUMS-v0.1.2-rc3.asc`
- Release key fingerprint:
  `5744BDF701AFDCF43983AB96B87F9907D27EC983`

## Required Checks

1. Download the installer, `SHA256SUMS-v0.1.2-rc3`,
   `SHA256SUMS-v0.1.2-rc3.asc`, `bitstar-release-key.asc`, and
   `verify-checksums.ps1` from the official GitHub release.
2. Verify the GPG signature for the manifest.
3. Verify the installer checksum.
4. Run the installer normally.
5. Confirm Start Menu entries exist for BitStar.
6. Open BitStar Launcher from the Start Menu.
7. Start the node from the launcher.
8. Show status from the launcher and record:
   - block height;
   - best block hash;
   - peer count;
   - initial block download state.
9. Create or load `wallet1`.
10. Generate one `bst1...` receiving address.
11. Run wallet backup from the launcher.
12. Stop the node from the launcher.
13. Uninstall BitStar from Windows Apps/Settings or the Start Menu uninstall
    shortcut.
14. Confirm the program files are removed.
15. Confirm `%LOCALAPPDATA%\BitStar` is not deleted by uninstall.
16. Confirm the wallet backup file still exists.

## Pass Criteria

The promotion repeat passes only if:

- GPG manifest verification passes;
- SHA256 checksum verification passes;
- installer completes without manual file copying;
- Start Menu launcher opens;
- node starts and reports the BitStar genesis chain;
- peer count is at least `1`, or a clear network/DNS explanation is recorded;
- wallet address generation works;
- wallet backup succeeds and the backup file exists;
- node stops cleanly;
- uninstall removes program files but preserves `%LOCALAPPDATA%\BitStar`.

## Fail Criteria

The promotion repeat fails if:

- GPG or SHA256 verification fails;
- installer cannot run on a normal Windows user profile;
- Start Menu launcher cannot open;
- launcher cannot start or stop the node;
- wallet backup fails without a clear warning;
- uninstall deletes the user data directory;
- the tester must manually edit private RPC credentials to complete the basic
  flow.

## Report Template

```text
BitStar Windows installer production promotion repeat

Release tag:
Tester:
Windows version:
Test date UTC:
Install method:

GPG manifest verification:
Checksum verification:
Installer opened:
Start Menu entries:
Launcher opened:
Node start:
Block height:
Best block:
Connection count:
Initial block download:
Wallet loaded or created:
Receiving address generated:
Wallet backup path:
Node stop:
Uninstall:
Program files removed:
Data directory preserved:
Wallet backup preserved:

Result: PASS/FAIL
Notes:
```

## Promotion Decision

If this manual repeat passes, BitStar can mark the `v0.1.2-rc3` Windows
installer as externally repeated for launcher usability. It should still remain
an unsigned release candidate until Windows Authenticode signing and
previous-installer upgrade testing are complete.
