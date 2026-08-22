# BitStar Production Readiness Plan

This document defines the path from the current public bootstrap to a
production-grade BitStar launch.

## Current Classification

Status: public bootstrap / early public test.

BitStar has source code, public seed nodes, a basic explorer, a public website,
and a Stratum-compatible solo test pool. It is not yet a final production
release. The current chain should be described honestly as a bootstrap chain
until the project completes the release and launch gates below.

See [current-status-audit.md](current-status-audit.md) for the latest
point-in-time audit of public services, release artifacts, and remaining
production gaps.
Use [operator-runbook.md](operator-runbook.md) as the daily operating checklist
for seed nodes, explorer API, test pool, backups, and release verification.

As of August 22, 2026, seed1 and seed2 are synchronized at height `5` with best
block:

```text
00000e7ed0c7df4e0db2d66c8d0031042e1ad66f5a8e3bf3e23a8e6a151c502d
```

The software still reports the pre-release warning:

```text
This is a pre-release test build - use at your own risk - do not use for mining or merchant applications
```

## Production Gates

### Gate 1: Source And Consensus Freeze

Definition of done:

- public repository is the canonical source
- network parameters are documented and reviewed
- genesis hash, message magic, ports, address prefixes, subsidy schedule, and
  halving interval are frozen for the intended release
- no private chain data is packaged with binaries
- upstream Bitcoin Core origin is disclosed
- all BitStar-specific patches are isolated and reviewable

Current status: partially complete.

### Gate 2: Fair Launch Decision

Definition of done:

- decide whether the current bootstrap chain remains the public chain or whether
  a final fair-launch reset will be performed
- if continuing the current chain, disclose all early mining and bootstrap
  history
- if resetting, publish the exact reset time, source commit, binaries,
  checksums, seed nodes, explorer, and mining instructions before block 1 can be
  mined
- publish the final no-premine statement

Current status: pending decision.

Recommended path: treat the current chain as public bootstrap testing, then
perform one final coordinated launch only after signed releases and public
instructions are ready.

### Gate 3: Stable Seed Network

Definition of done:

- at least two public seed nodes in separate regions
- P2P port `21333` open and monitored
- RPC port `21332` bound to localhost only
- node services start automatically after reboot
- logs are rotated
- disk, memory, CPU, and uptime alerts are active
- `bitstar-operator-status` is installed and used for daily checks
- chain height and best hash match across seed nodes
- at least one independent third-party node has joined and synced

Current status: seed1 and seed2 are online; independent nodes are still needed.

### Gate 4: Release Engineering

Definition of done:

- Windows and Linux binaries built from a documented source commit
- release artifacts have SHA256 checksums
- release notes explain exact status and risks
- signing key is published
- checksums or release manifests are signed
- clean install and upgrade tests pass
- wallet backup and restore path is documented
- operator verification record is completed for the exact artifacts
- no test wallet or chain data is bundled

Current status: bootstrap binaries exist. The Windows launcher package and
Linux x86_64 server package are published for `v0.1.1-bootstrap`, with SHA256
checksum files, helper verification scripts, and manifest signing helpers.
Actual signed production release artifacts are still pending until a dedicated
release signing key is created and `SHA256SUMS.asc` is published.

### Gate 5: Explorer

Definition of done:

- homepage shows live height, best block, difficulty, peers, supply estimate,
  and seed status
- block lookup by height and hash works
- transaction lookup works
- address lookup works
- API has stable endpoints and caching
- explorer has a clear disclaimer while the network is pre-release
- explorer is monitored and recovers after reboot

Current status: basic explorer exists; professional explorer features are
pending.

### Gate 6: Mining And Pool Compatibility

Definition of done:

- solo mining and Stratum compatibility are documented
- test pool is clearly labeled as solo/test
- pool software validates BitStar `bst1` payout addresses
- shares are accepted at the configured share difficulty
- candidate blocks can be submitted through `submitblock`
- production pool design includes dashboard, accounting, payout rules, payout
  maturity, worker stats, and abuse limits
- no official pool is announced until payout accounting is tested

Current status: solo/test Stratum endpoint is live; production pool system is
pending.

### Gate 7: Security Review

Definition of done:

- RPC is never exposed publicly
- seed servers use firewall allowlists for admin access
- SSH password login is disabled
- unattended security updates are enabled or patch schedule is documented
- service users run with least privilege
- private keys, wallet files, RPC passwords, and deployment tokens are not in
  the repository
- at least one external reviewer checks the BitStar-specific patches
- known limitations are listed publicly
- operator runbook is current and has been followed for the public seed nodes

Current status: operational hardening is partially complete; external review is
pending.

### Gate 8: Public Identity And Communication

Definition of done:

- website has project overview, downloads, explorer, mining guide, node guide,
  pool status, and risk warnings
- GitHub README links to the website and docs
- launch announcement is dated and archived
- contact path and issue tracker are public
- social/community channels exist before exchange outreach

Current status: website and docs exist; public communication cadence is pending.

### Gate 9: Exchange / Broker Readiness

Definition of done:

- production release is signed and stable
- explorer is reliable
- there are independent nodes and miners
- wallets are documented and tested
- legal/compliance summary is prepared
- project ownership and support contact are clear
- supply, premine status, and early mining history are transparent
- there is no promise of listing, liquidity, price, or profit

Current status: not ready.

## Immediate Next Steps

1. Keep seed1 and seed2 synchronized and monitored.
2. Run the operator runbook on seed1 and seed2 after each infrastructure change.
3. Create the dedicated release signing key, publish its fingerprint, and
   publish `SHA256SUMS.asc` for the current release.
4. Decide the fair launch path: continue with full disclosure, or reset once for
   a final public launch.
5. Upgrade the explorer from status-only to block, transaction, and address
   search.
6. Keep the current pool labeled as solo/test until a payout/accounting system
   exists.
7. Invite independent node operators to join and verify the network.
