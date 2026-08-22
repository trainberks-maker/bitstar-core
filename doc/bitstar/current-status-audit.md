# BitStar Current Status Audit

This audit records the current public state of BitStar and the work still
required before the project can be described as production-ready.

Date: 2026-08-22

## Classification

Current status: public bootstrap / early public test.

BitStar is not a final production release yet. The network, website, signed
bootstrap release artifacts, seed nodes, explorer, and solo test pool are live
enough for public testing, but the project still requires broader review,
stronger explorer functionality, independent nodes, final release-candidate
testing, and a production-grade pool or a clear decision to keep the pool
test-only.

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

### Release Artifacts

Latest bootstrap release:

- Tag: `v0.1.1-bootstrap`
- Release URL:
  `https://github.com/trainberks-maker/bitstar-core/releases/tag/v0.1.1-bootstrap`
- Assets:
  - `BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz`
  - `BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz.sha256`
  - `BitStar_Windows_v0.1.1-bootstrap.zip`
  - `BitStar_Windows_v0.1.1-bootstrap.zip.sha256`
  - `SHA256SUMS`
  - `SHA256SUMS.asc`
  - `bitstar-release-key.asc`
  - `verify-checksums.ps1`
  - `verify-checksums.sh`

Current published SHA256 values:

- `BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz`:
  `24ec7ec5cc9ff15d0ed94a544a4ea6d860368f468626411a0df97c8f2ff5ef27`
- `BitStar_Windows_v0.1.1-bootstrap.zip`:
  `9cd8e559da3a8a8b92d6df92e5007923e226987b9087c9256180bdae1b76831d`

Bootstrap release signature status:

- Release key: `BitStar Release <release@bitstarcoin.org>`
- Fingerprint:
  `5744BDF701AFDCF43983AB96B87F9907D27EC983`
- Signed manifest: `SHA256SUMS.asc` is published.
- Public key: `bitstar-release-key.asc` is published.
- Readiness gate result:
  `Result: release artifacts are signed and checksum verified.`

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

The current releases are bootstrap releases. They are useful for testing and
coordination, but they are not final stable releases.

Remaining work:

- complete clean install smoke tests for Windows and Linux `v0.1.1-bootstrap`
- create a release candidate tag after the build matrix is complete
- remove or update pre-release warnings only when production gates are complete

### 2. Signing And Verification

The `v0.1.1-bootstrap` release now has checksum verification documentation,
helper scripts, a published public release key, and a GPG-signed
`SHA256SUMS.asc` manifest. This makes the bootstrap artifacts signed and
checksum-verifiable, but it does not make BitStar a final production release.

Remaining work:

- complete independent verification of the signed artifacts
- repeat the signing process for the next release candidate or final release
- add Windows Authenticode signing when a code-signing certificate exists
- document key rotation and maintainer responsibility

### 3. Pool Status

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

### 4. Explorer Status

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

### 5. Security Review

Operational hardening has started, but the BitStar-specific patches still need
external review.

Remaining work:

- external code review of consensus, chain parameters, address prefixes, seed
  configuration, and wallet changes
- review of VPS firewall, SSH, service permissions, and backups
- review that no private keys, wallets, RPC passwords, or deployment tokens are
  in releases or repository history

### 6. Network Decentralization

The network has two public seed nodes, but production credibility requires
independent participants.

Remaining work:

- at least one third-party node joins and syncs
- independent miners test solo mining
- independent operators verify release checksums and publish results
- documented bootstrap peers beyond founder-operated infrastructure

### 7. Exchange Or Broker Readiness

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

1. Run a signed release test matrix for Windows and Linux from clean datadirs.
2. Record at least one independent verification of the release signature and
   checksums.
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
the final production launch until independent verification, explorer
improvements, third-party nodes, release-candidate testing, and public launch
policy are complete.
