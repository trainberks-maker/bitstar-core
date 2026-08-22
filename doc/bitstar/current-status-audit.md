# BitStar Current Status Audit

This audit records the current public state of BitStar and the work still
required before the project can be described as production-ready.

Date: 2026-08-22

## Classification

Current status: public bootstrap / early public test.

BitStar is not a final production release yet. The network, website, signed
release-candidate artifacts, seed nodes, explorer, and solo test pool are live
enough for public testing, but the project still requires broader review,
stronger explorer functionality, independent nodes, independent verification,
and a production-grade pool or a clear decision to keep the pool test-only.

## Verified Public Facts

### Source Repository

- Canonical repository: `https://github.com/trainberks-maker/bitstar-core`
- Public branch: `master`
- Recent production-readiness commits:
  - `e44ea5deb0` Improve BitStar release signing workflow
  - `47e0e4a2c9` Add BitStar release package hygiene audit
  - `30fa517a97` Add BitStar release signing readiness checks
  - `9d79a03639` Add BitStar operator runbook
  - `4149c7078e` Add BitStar release verification guide
  - `7292574d9d` Add Windows launcher helper scripts
  - `bd2089854f` Add BitStar VPS hardening scripts

### Website

- Official website: `https://bitstarcoin.org`
- Website routes exist for:
  - `/`
  - `/explorer`
  - `/launch`
  - `/mining`
  - `/pool`
- The website links the latest Windows bootstrap launcher, Linux x86_64 server
  package, and checksum verification files.
- A Windows installer plan exists, but no installer download is published yet.

### Release Artifacts

Latest release candidate:

- Tag: `v0.1.2-rc2`
- Source commit: `75b5e47311269bcc0ea6eb5cf7cdb4726eac4f3f`
- Release URL:
  `https://github.com/trainberks-maker/bitstar-core/releases/tag/v0.1.2-rc2`
- Assets:
  - `BitStar_Windows_v0.1.2-rc2.zip`
  - `BitStar_Windows_v0.1.2-rc2.zip.sha256`
  - `BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz`
  - `BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz.sha256`
  - `SHA256SUMS-v0.1.2-rc2`
  - `SHA256SUMS-v0.1.2-rc2.asc`
  - `bitstar-release-key.asc`
  - `verify-checksums.ps1`
  - `verify-checksums.sh`
  - `scan-release-package.ps1`
  - `scan-release-package.sh`
  - `check-release-readiness.ps1`
  - `check-release-readiness.sh`

Current published SHA256 values:

- `BitStar_Windows_v0.1.2-rc2.zip`:
  `416c5232a7155ba85fcdfd1b4005bf184d75055433193b214cf8d7a1cf57dd46`
- `BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz`:
  `a13e9ec2c13a97f169f6d9e3c37256c27caa878dbe08d9a971da2be05f774392`

Release-candidate signature status:

- Release key: `BitStar Release <release@bitstarcoin.org>`
- Fingerprint:
  `5744BDF701AFDCF43983AB96B87F9907D27EC983`
- Signed manifest: `SHA256SUMS-v0.1.2-rc2.asc` is published.
- Public key: `bitstar-release-key.asc` is published.
- Readiness gate result:
  `Result: release artifacts are signed and checksum verified.`
- Smoke test result: Windows launcher clean test passed; Windows and Linux
  synthetic upgrades from `v0.1.1-bootstrap` to `v0.1.2-rc2` passed; Linux
  x86_64 clean temporary-datadir smoke test passed with two seed connections.
- Windows installer status: NSIS installer scaffold and build validation helper
  exist; no installer artifact is published in `v0.1.2-rc2`.

### Network Parameters

- Name: BitStar
- Ticker: BST
- Supply cap: 21,000,000 BST
- Proof-of-work: SHA256d
- Target block time: 10 minutes
- Halving interval: 210,000 blocks
- Initial subsidy: 50 BST
- P2P port: `21333`
- RPC port: `21332`
- Bech32 prefix: `bst`
- Genesis hash:
  `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`

### Seed Nodes And Services

Public seed nodes:

- `seed1.bitstarcoin.org:21333`
- `seed2.bitstarcoin.org:21333`

Verified port status:

- `seed1.bitstarcoin.org:21333`: reachable
- `seed2.bitstarcoin.org:21333`: reachable
- `pool.bitstarcoin.org:3333`: reachable
- `seed2.bitstarcoin.org:8090`: reachable

Verified service status:

- seed1:
  - `bitstard`: active
  - `bitstar-healthcheck.timer`: active
  - public P2P listens on `0.0.0.0:21333`
  - RPC listens on `127.0.0.1:21332`
- seed2:
  - `bitstard`: active
  - `bitstar-stratum-pool`: active
  - `bitstar-explorer-api`: active
  - `bitstar-healthcheck.timer`: active
  - public P2P listens on `0.0.0.0:21333`
  - Stratum test pool listens on `0.0.0.0:3333`
  - explorer API listens on `0.0.0.0:8090`
  - RPC listens on `127.0.0.1:21332`

### Explorer API Snapshot

Public explorer API:

- `http://seed2.bitstarcoin.org:8090/api/summary`

Current public snapshot:

- Chain: `main`
- Height: `1136`
- Headers: `1136`
- Best block:
  `000009f1293ce4e68983535421f0701ed424104699f0f23ae5dca6b2885cf4f5`
- Difficulty: `0.000244140625`
- Connections: `2`
- Initial block download: `false`
- Warning:

```text
This is a pre-release test build - use at your own risk - do not use for mining or merchant applications
```

## What Is Not Production-Ready Yet

### 1. Release Status

The current release is a signed release candidate. It is useful for public
testing and coordination, but it is not a final stable production release.

Remaining work:

- record and archive an independent third-party verification of `v0.1.2-rc2`
  using [independent-verification-pack.md](independent-verification-pack.md)
- repeat the Windows and Linux upgrade tests independently from the latest
  bootstrap data directories
- remove or update pre-release warnings only when production gates are complete

### 2. Signing And Verification

The `v0.1.2-rc2` release candidate has checksum verification documentation,
helper scripts, a published public release key, and a GPG-signed
`SHA256SUMS-v0.1.2-rc2.asc` manifest. This makes the release-candidate
artifacts signed and checksum-verifiable, but it does not make BitStar a final
production release.

Remaining work:

- invite an outside tester to run
  [independent-verification-pack.md](independent-verification-pack.md) and
  publish the signed-artifact verification result
- repeat the signing process for every later release candidate or final release
- add Windows Authenticode signing when a code-signing certificate exists
- document key rotation and maintainer responsibility

### 3. Launcher And Installer Status

The Windows launcher exists and is included in the release-candidate zip. It is
usable for testing, but it is not yet a production-grade installer flow.

Remaining work:

- build the NSIS installer from the verified Windows package
- test clean install, Start Menu launcher start/stop, and uninstall
- confirm uninstall leaves `%LOCALAPPDATA%\BitStar` untouched
- add installer checksum to the signed release manifest
- add Windows Authenticode signing when a certificate exists
- publish installer download only after the launcher production checklist passes

### 4. Pool Status

The current pool endpoint is a solo/test Stratum compatibility endpoint. It is
not a full public mining pool.

Remaining work before an official production pool:

- worker dashboard
- share accounting
- payout accounting
- payout maturity rules
- wallet isolation
- abuse limits
- logging and alerts
- clear fee policy
- public pool terms

### 5. Explorer Status

The explorer is useful as a basic public status surface, but it is not yet a
professional explorer comparable to mature block explorers.

Remaining work:

- block search by height and hash in the public UI
- transaction search
- address search
- supply and coinbase maturity views
- peer and seed status display
- API caching and rate limits
- index persistence and restart recovery tests

### 6. Security Review

Operational hardening has started, but the BitStar-specific patches still need
external review.

Remaining work:

- external code review of consensus, chain parameters, address prefixes, seed
  configuration, and wallet changes
- review of VPS firewall, SSH, service permissions, and backups
- review that no private keys, wallets, RPC passwords, or deployment tokens are
  in releases or repository history

### 7. Network Decentralization

The network has two public seed nodes, but production credibility requires
independent participants.

Remaining work:

- at least one third-party node joins and syncs
- independent miners test solo mining
- independent operators verify release checksums and publish results
- documented bootstrap peers beyond founder-operated infrastructure

### 8. Exchange Or Broker Readiness

BitStar is not ready for serious exchange or broker outreach yet.

Remaining work:

- signed and stable production release
- reliable explorer
- independent nodes and miners
- clear ownership and support contact
- legal/compliance summary
- public disclosure of launch history
- no promises of listing, liquidity, price, or profit

## Recommended Next Work Order

1. Record at least one independent verification of the release signature and
   checksums using
   [independent-verification-pack.md](independent-verification-pack.md).
2. Repeat the recorded Windows and Linux upgrade tests independently from
   earlier bootstrap data directories, and archive the results in
   [clean-install-upgrade-test.md](clean-install-upgrade-test.md).
3. Upgrade the explorer from status-only to block, transaction, and address
   lookup.
4. Keep the current pool labeled as solo/test, or build a real dashboard and
   payout accounting system before calling it official.
5. Invite independent node operators and miners.
6. Decide final fair-launch policy: continue current bootstrap chain with full
   disclosure, or perform one final reset after signed release artifacts are
   ready.

## Current Recommendation

Continue treating the current chain as a public bootstrap chain. Do not call it
the final production launch until independent verification results, explorer
improvements, third-party nodes, release-candidate testing, and public launch
policy are complete.
