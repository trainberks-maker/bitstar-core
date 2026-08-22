# BitStar Clean Install And Upgrade Test

This record must be completed for every release candidate and final release
before BitStar is described as production-ready.

## Scope

Test each release artifact from an empty data directory and from a previous
bootstrap or release-candidate data directory. Do not reuse a developer wallet,
private chain directory, RPC password, SSH key, or deployment token in any test
package.

## Required Test Matrix

| Platform | Artifact | Clean install | Upgrade | Wallet backup | Result |
| --- | --- | --- | --- | --- | --- |
| Windows x86_64 | `BitStar_Windows_<version>.zip` | pending | pending | pending | pending |
| Linux x86_64 | `BitStar_Linux_x86_64_<version>.tar.gz` | pending | pending | pending | pending |
| Linux arm64 | `BitStar_Linux_arm64_<version>.tar.gz` | pending | pending | pending | pending |

Latest recorded release-candidate checks:

| Platform | Artifact | Clean install | Upgrade | Wallet backup | Result |
| --- | --- | --- | --- | --- | --- |
| Windows x86_64 | `BitStar_Windows_v0.1.2-rc2.zip` | passed | synthetic `v0.1.1-bootstrap` upgrade passed; independent repeat pending | launcher backup action smoke-tested | pre-release pass |
| Linux x86_64 | `BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz` | passed | synthetic `v0.1.1-bootstrap` upgrade passed; independent repeat pending | not applicable for headless package | pre-release pass |
| Linux arm64 | `BitStar_Linux_arm64_<version>.tar.gz` | pending | pending | pending | pending |

Linux arm64 can remain pending for a bootstrap release, but it should be
completed before a broader production launch because many VPS and small node
operators use arm64 systems.

## Windows Clean Install

1. Download the Windows zip, `SHA256SUMS-v0.1.2-rc2`,
   `SHA256SUMS-v0.1.2-rc2.asc`, and `bitstar-release-key.asc` from the
   official release page.
2. Verify the GPG signature and checksums using
   [release-verification.md](release-verification.md).
3. Extract the zip into a new folder.
4. Confirm these files exist:
   - `bitstar.exe`
   - `bitstard.exe`
   - `bitstar-cli.exe`
   - `BitStar-Launcher.bat`
   - `BitStar-Launcher.ps1`
   - `README.md`
5. Start `BitStar-Launcher.bat`.
6. Choose `Ensure config`.
7. Choose `Start node`.
8. Choose `Show status`.
9. Confirm:
   - genesis hash is
     `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`
   - the node reaches at least one peer
   - block height increases or matches seed nodes
   - RPC is available only locally
10. Create or load a test wallet, generate one `bst1` address, and run wallet
    backup from the launcher.
11. Stop the node cleanly from the launcher.

Record the Windows result here:

```text
Version:
Source commit:
Artifact SHA256:
Test date:
Tester:
Clean data directory:
Peers:
Block height:
Best block:
Wallet backup path:
Result:
Notes:
```

## Linux Clean Install

1. Download the Linux tarball, `SHA256SUMS-v0.1.2-rc2`,
   `SHA256SUMS-v0.1.2-rc2.asc`, and `bitstar-release-key.asc`.
2. Verify the signature and checksums.
3. Extract into a new folder.
4. Start with an empty data directory:

```sh
mkdir -p /tmp/bitstar-clean-test
./bin/bitstard -datadir=/tmp/bitstar-clean-test -server=1 -listen=1 \
  -addnode=seed1.bitstarcoin.org:21333 \
  -addnode=seed2.bitstarcoin.org:21333 -daemon
```

5. Verify the node:

```sh
./bin/bitstar-cli -datadir=/tmp/bitstar-clean-test getblockhash 0
./bin/bitstar-cli -datadir=/tmp/bitstar-clean-test getblockchaininfo
./bin/bitstar-cli -datadir=/tmp/bitstar-clean-test getconnectioncount
```

6. Stop cleanly:

```sh
./bin/bitstar-cli -datadir=/tmp/bitstar-clean-test stop
```

Record the Linux result here:

```text
Version: v0.1.2-rc2
Source commit: 75b5e47311269bcc0ea6eb5cf7cdb4726eac4f3f
Artifact SHA256: a13e9ec2c13a97f169f6d9e3c37256c27caa878dbe08d9a971da2be05f774392
Test date: 2026-08-22
Tester: BitStar maintainer
Clean data directory: /tmp/bitstar-linux-rc2-smoke
Peers: 2
Block height: 1136
Best block: 000009f1293ce4e68983535421f0701ed424104699f0f23ae5dca6b2885cf4f5
Result: PASS
Notes: Headless Linux package started from a clean temporary datadir, RPC became ready, genesis and chain info matched the public network, two seed connections were observed, and the node stopped cleanly.
```

## Upgrade Test

Run this after clean install succeeds.

1. Start an older bootstrap or release-candidate data directory.
2. Record height, best block, wallet list, and peer count.
3. Stop the old node cleanly.
4. Start the new release against the same data directory.
5. Confirm:
   - block database opens cleanly
   - chain continues from the same best block or better
   - wallets load only when expected
   - no wallet backup is overwritten
   - peer count recovers
   - no private RPC settings are exposed
6. Stop the new node cleanly.

Record upgrade results here:

```text
Old version:
New version:
Source commit:
Test date:
Tester:
Before height:
After height:
Before best block:
After best block:
Wallet backup verified:
Result:
Notes:
```

```text
Old version: v0.1.1-bootstrap
New version: v0.1.2-rc2
Source commit: 75b5e47311269bcc0ea6eb5cf7cdb4726eac4f3f
Test date: 2026-08-22
Tester: BitStar maintainer
Test data directory: C:\Users\bajra\Documents\Codex\2026-08-21\https-github-com-bitcoin-bitcoin-https\outputs\upgrade-test-v0.1.1-to-v0.1.2-rc2-20260822-160210\data
Before height: 967
After height: 1136
Before best block: 000009747c95aabad1a2380d14c1919be7f269552a30b090f5d5b1ed086dda60
After best block: 000009f1293ce4e68983535421f0701ed424104699f0f23ae5dca6b2885cf4f5
Before peers: 2
After peers: 2
Genesis hash verified: 00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49
Wallet backup verified: not applicable; no wallet was loaded in this synthetic upgrade test
Result: PASS
Notes: v0.1.1-bootstrap opened a fresh test datadir, synced from public seeds, stopped cleanly, and v0.1.2-rc2 reopened the same datadir without reindex or wallet changes. This is an internal synthetic upgrade smoke test and still needs an independent repeat before production promotion.
```

```text
Old version: v0.1.1-bootstrap
New version: v0.1.2-rc2
Source commit: 75b5e47311269bcc0ea6eb5cf7cdb4726eac4f3f
Test date: 2026-08-22
Tester: BitStar maintainer
Host: seed2.bitstarcoin.org
Test data directory: /tmp/bitstar-linux-upgrade-v0.1.1-to-v0.1.2-rc2-20260822-140924/data
Old artifact SHA256: 24ec7ec5cc9ff15d0ed94a544a4ea6d860368f468626411a0df97c8f2ff5ef27
New artifact SHA256: a13e9ec2c13a97f169f6d9e3c37256c27caa878dbe08d9a971da2be05f774392
Before height: 1136
After height: 1136
Before best block: 000009f1293ce4e68983535421f0701ed424104699f0f23ae5dca6b2885cf4f5
After best block: 000009f1293ce4e68983535421f0701ed424104699f0f23ae5dca6b2885cf4f5
Before peers: 2
After peers: 2
Genesis hash verified: 00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49
Wallet backup verified: not applicable; no wallet was loaded and the v0.1.1 Linux package does not expose listwallets RPC
Result: PASS
Notes: Linux v0.1.1-bootstrap opened a synthetic test datadir, synced from public seeds, stopped cleanly, and Linux v0.1.2-rc2 reopened the same datadir without reindex or wallet changes. This is an internal synthetic upgrade smoke test and still needs an independent repeat before production promotion.
```

## Release Gate

A release candidate can move forward only when:

- Windows and Linux clean install tests are recorded;
- upgrade tests are recorded from the latest public bootstrap release;
- release signature and checksums verify on both Windows and Linux;
- the package hygiene audit reports no private wallets, chain data, RPC
  credentials, SSH keys, or deployment tokens;
- known limitations are written in the release notes.
