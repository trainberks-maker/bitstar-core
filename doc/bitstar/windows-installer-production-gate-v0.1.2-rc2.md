# BitStar Windows Installer Production Gate - v0.1.2-rc2

Date: 2026-08-22 17:17:10 +02:00

Installer artifact: "BitStar_Core_Setup_v0.1.2-rc2.exe"

Expected SHA256: `b1a8d3aea370beb6126daf37e70902e53cef29ec0e7778cdfd89c033d94330ad`
Actual SHA256: `b1a8d3aea370beb6126daf37e70902e53cef29ec0e7778cdfd89c033d94330ad`

## Result

Overall: **PASS**

## Checks

| Check | Result | Notes |
| --- | --- | --- |
| installer exists | PASS | found |
| installer SHA256 | PASS | b1a8d3aea370beb6126daf37e70902e53cef29ec0e7778cdfd89c033d94330ad |
| silent clean install | PASS | exit code 0 |
| installed file set | PASS | all required files present |
| registry install dir | PASS | %TEMP%\bitstar-installer-gate-20260822-171652\install |
| registry uninstall entry | PASS | BitStar Core |
| Start Menu shortcuts | PASS | all shortcut targets valid |
| launcher start node | PASS | RPC ready on isolated datadir |
| node chain identity | PASS | chain=main, blocks=152, best=000008e8b0cb9fa8a7aa99222448b0555846c1228ea5a31da786708511f659b8 |
| wallet backup | PASS | %TEMP%\bitstar-installer-gate-20260822-171652\data\wallet-backups\20260822-171659\gatewallet.dat |
| launcher stop node | PASS | RPC stopped responding after stop |
| silent uninstall | PASS | exit code 0 |
| install directory removed | PASS | %TEMP%\bitstar-installer-gate-20260822-171652\install |
| test data preserved by uninstall | PASS | %TEMP%\bitstar-installer-gate-20260822-171652\data |
| wallet backup survives uninstall | PASS | %TEMP%\bitstar-installer-gate-20260822-171652\data\wallet-backups\20260822-171659\gatewallet.dat |

## Scope

- Test install directory: `%TEMP%\bitstar-installer-gate-20260822-171652\install`
- Test data directory: `%TEMP%\bitstar-installer-gate-20260822-171652\data`
- RPC port: `21452`
- P2P port: `21453`
- Existing user Start Menu and registry state were backed up before the test and restored during cleanup.
- The real %LOCALAPPDATA%\BitStar data directory was not used for node or wallet operations.

## Remaining Production Gaps

- Windows Authenticode signing is still pending.
- This is an internal local gate, not an independent third-party audit.
- A human should still repeat one GUI launch from a fresh Windows profile before final production promotion.
