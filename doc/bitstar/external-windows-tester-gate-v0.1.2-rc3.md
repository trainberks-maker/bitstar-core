# BitStar External Windows Tester Gate

Target release: `v0.1.2-rc3`

Release URL:
`https://github.com/trainberks-maker/bitstar-core/releases/tag/v0.1.2-rc3`

This checklist is for a tester using a separate Windows PC. The goal is to
confirm that a normal user can download BitStar, verify the package, install
it, start the node, create a wallet address, back up the wallet, mine through
the public test pool, and uninstall cleanly.

This is still a pre-release test. Do not use this build for exchange deposits,
merchant payments, custody, or production funds.

## Artifacts

Use only files from the official release page.

| File | SHA256 |
| --- | --- |
| `BitStar_Core_Setup_v0.1.2-rc3.exe` | `954ed1bb71c51daef237cd0de8cf293165d38c74d0fff24e8861b5c1c343ce42` |
| `BitStar_Windows_v0.1.2-rc3.zip` | `491fd62654f0a883db5ed7da33c38c13a9152240441cd57540037a088eb01320` |

Release key fingerprint:

```text
5744BDF701AFDCF43983AB96B87F9907D27EC983
```

## Safety Rules

- Do not share private keys, wallet seed words, RPC passwords, SSH keys, or API
  tokens.
- Use a new test wallet only.
- Back up the wallet before mining for more than a short test.
- Keep RPC local. Do not open port `21332` to the internet.
- Windows Firewall may ask for permission the first time the node starts.

## Step 1: Download And Verify

Download these files into one folder, for example `Downloads\BitStar-rc3-test`:

- `BitStar_Core_Setup_v0.1.2-rc3.exe`
- `SHA256SUMS-v0.1.2-rc3`
- `SHA256SUMS-v0.1.2-rc3.asc`
- `bitstar-release-key.asc`
- `verify-checksums.ps1`

Open PowerShell in that folder and run:

```powershell
gpg --import .\bitstar-release-key.asc
gpg --fingerprint "BitStar Release"
gpg --verify .\SHA256SUMS-v0.1.2-rc3.asc .\SHA256SUMS-v0.1.2-rc3
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS-v0.1.2-rc3
```

Pass condition:

- GPG shows the expected fingerprint.
- The signature verifies.
- The installer checksum passes.

If GPG is not installed, run at least the built-in Windows checksum check:

```powershell
Get-FileHash .\BitStar_Core_Setup_v0.1.2-rc3.exe -Algorithm SHA256
```

The hash must equal:

```text
954ed1bb71c51daef237cd0de8cf293165d38c74d0fff24e8861b5c1c343ce42
```

## Step 2: Install

Double-click:

```text
BitStar_Core_Setup_v0.1.2-rc3.exe
```

Install with the default options.

Pass condition:

- BitStar appears in the Start Menu.
- The install folder contains `bitstard.exe`, `bitstar-cli.exe`,
  `BitStar-Launcher.bat`, `Start-BitStar-Node.bat`,
  `Check-BitStar-Status.bat`, `Show-BitStar-Wallet-Address.bat`, and
  `Stop-BitStar-Node.bat`.

## Step 3: Start The Node

Open the Start Menu and run:

```text
BitStar Launcher
```

Choose:

```text
1
```

Pass condition:

- The launcher says the node started, or says the node is already running.
- A console window may remain open with BitStar node logs.

## Step 4: Check Status

In the launcher choose:

```text
2
```

Pass condition:

- Chain is `main`.
- Block count is greater than `0`.
- Connection count is at least `1`.
- No RPC connection error appears.

If using PowerShell manually:

```powershell
cd "$env:LOCALAPPDATA\Programs\BitStar Core"
.\bitstar-cli.exe -datadir="$env:LOCALAPPDATA\BitStar" getblockchaininfo
.\bitstar-cli.exe -datadir="$env:LOCALAPPDATA\BitStar" getconnectioncount
```

## Step 5: Create Or Show Wallet Address

In the launcher choose:

```text
3
```

Pass condition:

- A wallet named `wallet1` is created or loaded.
- A receiving address is printed.
- The address starts with `bst1`.

Record the address in the report. Do not record private keys.

## Step 6: Back Up Wallet

In the launcher choose:

```text
4
```

Pass condition:

- A backup file is created under:

```text
%LOCALAPPDATA%\BitStar\wallet-backups
```

## Step 7: Optional Mining Smoke Test

This test only checks that the public pool accepts shares from a normal Windows
PC. It is not a payout-system test.

Download and extract cpuminer into `Downloads\cpuminer-opt-26.1-windows`.

In PowerShell, replace `YOUR_BST_ADDRESS` with the address from Step 5:

```powershell
cd "$env:USERPROFILE\Downloads\cpuminer-opt-26.1-windows"
.\cpuminer-sse2.exe -a sha256d -o stratum+tcp://pool.bitstarcoin.org:3333 -u YOUR_BST_ADDRESS -p x -t 2
```

If `cpuminer-sse2.exe` is not present, list available miners:

```powershell
Get-ChildItem "$env:USERPROFILE\Downloads" -Recurse -Filter "cpuminer*.exe" | Select-Object FullName
```

Then run the available `.exe` from its real folder.

Pass condition:

- The miner connects to `pool.bitstarcoin.org:3333`.
- Shares show `Accepted`.
- If a block is found, it may show `BLOCK SOLVED`.

Stop the miner with `Ctrl+C` after a short test.

## Step 8: Stop The Node

In the launcher choose:

```text
6
```

Pass condition:

- The node stops cleanly.

Manual PowerShell command:

```powershell
cd "$env:LOCALAPPDATA\Programs\BitStar Core"
.\bitstar-cli.exe -datadir="$env:LOCALAPPDATA\BitStar" stop
```

## Step 9: Uninstall Cleanly

Use Windows Settings or the BitStar uninstaller.

Pass condition:

- Program files are removed.
- Wallet and chain data remain under `%LOCALAPPDATA%\BitStar`.
- Wallet backups remain under `%LOCALAPPDATA%\BitStar\wallet-backups`.

This behavior is intentional. Uninstalling the program must not delete a user's
wallet data.

## Result Template

Open a GitHub issue with this template:

`https://github.com/trainberks-maker/bitstar-core/issues/new?template=independent_verification.yml`

Paste the result:

```text
BitStar external Windows tester gate

Tester:
Date UTC:
Windows version:
Release tag: v0.1.2-rc3
Artifact: BitStar_Core_Setup_v0.1.2-rc3.exe
Installer SHA256 verified: PASS/FAIL
GPG manifest verified: PASS/FAIL/NOT INSTALLED
Install completed: PASS/FAIL
Start Menu launcher opened: PASS/FAIL
Node start: PASS/FAIL
Chain: main/other
Block height:
Connection count:
Wallet address created: PASS/FAIL
Wallet address prefix: bst1/other
Wallet backup created: PASS/FAIL
Mining smoke test performed: yes/no
Mining shares accepted: PASS/FAIL/NOT TESTED
Node stop: PASS/FAIL
Uninstall clean: PASS/FAIL
Wallet data preserved after uninstall: PASS/FAIL
Overall result: PASS/FAIL
Notes:
```

## Promotion Rule

`v0.1.2-rc3` should not be promoted beyond pre-release until at least one
external Windows tester publishes a passing result, and any failure reports are
reviewed.
