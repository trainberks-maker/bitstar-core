# BitStar Windows Installer Production Gate

Date: 2026-08-22 18:06:00 +02:00

Installer artifact: "BitStar_Core_Setup_v0.1.2-rc3.exe"

Actual SHA256: `954ed1bb71c51daef237cd0de8cf293165d38c74d0fff24e8861b5c1c343ce42`

## Result

Internal installer gate: **PASS**

Production promotion decision: **HOLD**

This record proves that the `v0.1.2-rc3` installer can install, start the
launcher flow, create/load a wallet, back up that wallet, stop the node, and
uninstall without deleting the test data directory. It does not yet promote the
installer to final production status.

## Checks

| Check | Result | Notes |
| --- | --- | --- |
| installer exists | PASS | found |
| installer SHA256 | PASS | 954ed1bb71c51daef237cd0de8cf293165d38c74d0fff24e8861b5c1c343ce42 |
| silent clean install | PASS | exit code 0 |
| installed file set | PASS | all required files present |
| registry install dir | PASS | %TEMP%\bitstar-installer-gate-20260822-180542\install |
| registry uninstall entry | PASS | BitStar Core |
| Start Menu shortcuts | PASS | all shortcut targets valid |
| launcher start node | PASS | RPC ready on isolated datadir |
| node chain identity | PASS | chain=main, blocks=104, best=0000005ad615237e7bddf3c517a8cc396da84db0db1a0833f4254cf4d1e0d7ba |
| wallet address action | PASS | Address: bst1qqm9065ge0wqsfea5gxm5msnsnqmw39xxy5gsg3 |
| wallet backup | PASS | %TEMP%\bitstar-installer-gate-20260822-180542\data\wallet-backups\20260822-180549\gatewallet.dat |
| launcher stop node | PASS | RPC stopped responding after stop |
| silent uninstall | PASS | exit code 0 |
| install directory removed | PASS | %TEMP%\bitstar-installer-gate-20260822-180542\install |
| test data preserved by uninstall | PASS | %TEMP%\bitstar-installer-gate-20260822-180542\data |
| wallet backup survives uninstall | PASS | %TEMP%\bitstar-installer-gate-20260822-180542\data\wallet-backups\20260822-180549\gatewallet.dat |

## Scope

- Test install directory: `%TEMP%\bitstar-installer-gate-20260822-180542\install`
- Test data directory: `%TEMP%\bitstar-installer-gate-20260822-180542\data`
- RPC port: `21452`
- P2P port: `21453`
- Existing user Start Menu and registry state were backed up before the test and restored during cleanup.
- The real %LOCALAPPDATA%\BitStar data directory was not used for node or wallet operations.

## Remaining Production Gaps

- Windows Authenticode signing is still pending.
- A dedicated independent installer repeat is still recommended.
- Previous-installer upgrade testing is still pending.
- The current Windows package is node and CLI-wallet only; a graphical wallet gate is required once `bitstar-qt.exe` is included.
- A human should still repeat a fresh Windows profile install before final production promotion.
