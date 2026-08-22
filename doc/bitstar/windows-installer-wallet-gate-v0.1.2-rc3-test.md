# BitStar Windows Installer Production Gate

Date: 2026-08-22 18:01:10 +02:00

Installer artifact: "BitStar_Core_Setup_v0.1.2-rc3-test.exe"

Actual SHA256: `638c151f34517968789812f0e43f355afa273cca7725edfde2eee2f93901b0e6`

## Result

Overall: **PASS**

## Checks

| Check | Result | Notes |
| --- | --- | --- |
| installer exists | PASS | found |
| installer SHA256 | PASS | 638c151f34517968789812f0e43f355afa273cca7725edfde2eee2f93901b0e6 |
| silent clean install | PASS | exit code 0 |
| installed file set | PASS | all required files present |
| registry install dir | PASS | %TEMP%\bitstar-installer-gate-20260822-180052\install |
| registry uninstall entry | PASS | BitStar Core |
| Start Menu shortcuts | PASS | all shortcut targets valid |
| launcher start node | PASS | RPC ready on isolated datadir |
| node chain identity | PASS | chain=main, blocks=105, best=00000ea2ca67529c81e47f3f0723886f80b3cfebb3ea6aaa59c0d062f3260419 |
| wallet address action | PASS | Address: bst1q6hm7r5zxv6zh69d38rxs74fx80p5cq288gd7wn |
| wallet backup | PASS | %TEMP%\bitstar-installer-gate-20260822-180052\data\wallet-backups\20260822-180100\gatewallet.dat |
| launcher stop node | PASS | RPC stopped responding after stop |
| silent uninstall | PASS | exit code 0 |
| install directory removed | PASS | %TEMP%\bitstar-installer-gate-20260822-180052\install |
| test data preserved by uninstall | PASS | %TEMP%\bitstar-installer-gate-20260822-180052\data |
| wallet backup survives uninstall | PASS | %TEMP%\bitstar-installer-gate-20260822-180052\data\wallet-backups\20260822-180100\gatewallet.dat |

## Scope

- Test install directory: `%TEMP%\bitstar-installer-gate-20260822-180052\install`
- Test data directory: `%TEMP%\bitstar-installer-gate-20260822-180052\data`
- RPC port: `21452`
- P2P port: `21453`
- Existing user Start Menu and registry state were backed up before the test and restored during cleanup.
- The real %LOCALAPPDATA%\BitStar data directory was not used for node or wallet operations.

## Remaining Production Gaps

- Windows Authenticode signing is still pending.
- This is an internal local gate, not an independent third-party audit.
- The current Windows package is node and CLI-wallet only; a graphical wallet gate is required once `bitstar-qt.exe` is included.
- A human should still repeat a fresh Windows profile install before final production promotion.

