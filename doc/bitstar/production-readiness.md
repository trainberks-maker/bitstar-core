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
Use [launcher-production-checklist.md](launcher-production-checklist.md) and
[windows-installer-plan.md](windows-installer-plan.md) for the path from the
current Windows zip package to a production-ready launcher installer.

As of August 22, 2026, seed1 and seed2 are synchronized at height `6062` with
best block:

```text
0000003a13dbf41f57a6d42c3af026d4031c0e5c17f06c2323016e0690e86eba
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
- at least one outside tester publishes a result using
  [independent-verification-pack.md](independent-verification-pack.md)
- release package hygiene audit confirms no private wallets, chain data, RPC
  credentials, SSH private keys, or deployment tokens are bundled
- no test wallet or chain data is bundled

Current status: `v0.1.2-rc3` is the current signed release candidate. The
Windows launcher zip, unsigned Windows installer, and Linux x86_64 server
package are published with SHA256 checksums, helper verification scripts, a
published public release key, and a GPG-signed
`SHA256SUMS-v0.1.2-rc3.asc` manifest. Windows clean install, Windows launcher,
Linux x86_64 clean temporary-datadir smoke, and synthetic Windows and Linux
upgrades from `v0.1.1-bootstrap` to `v0.1.2-rc2` are recorded in
[clean-install-upgrade-test.md](clean-install-upgrade-test.md).
An outside-tester checklist is now available in
[independent-verification-pack.md](independent-verification-pack.md). External
Windows verification report #1 has been archived and accepted as sufficient to
close the `v0.1.2-rc3` external Windows tester gate.
The Windows launcher production checklist and NSIS installer scaffold are
documented. A Windows NSIS installer has been built, smoke-tested, included in
the signed manifest, and published as an unsigned pre-release artifact. It has
not been promoted as a production installer. The current external Windows
tester repeat is documented in
[external-windows-tester-gate-v0.1.2-rc3.md](external-windows-tester-gate-v0.1.2-rc3.md).

The current release key fingerprint is:

```text
5744BDF701AFDCF43983AB96B87F9907D27EC983
```

The release-candidate readiness gate passes with:

```text
Result: release artifacts are signed and checksum verified.
```

This is still a signed pre-release candidate, not a final production release.
Remaining release-engineering work includes independent repeats of the Windows
and Linux upgrade tests, a Linux `v0.1.2-rc3` upgrade repeat, a clean-profile
manual Windows installer production promotion repeat, previous-installer
upgrade testing, Windows Authenticode signing, optional additional
outside-tester reports, and a repeat of the process for every later release
candidate or final release.

Clean install, Windows launcher, and full upgrade coverage must be recorded in
[clean-install-upgrade-test.md](clean-install-upgrade-test.md) before any release
candidate is promoted as production-ready.

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

Current status: solo/test Stratum endpoint is live. An external Windows miner
has connected to `pool.bitstarcoin.org:3333` and received accepted shares; see
[external-mining-pool-verification-v0.1.2-rc3.md](external-mining-pool-verification-v0.1.2-rc3.md).
The production pool system is still pending.

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
3. Keep external verification open for optional additional testers, and
   complete the upgrade matrix in
   [clean-install-upgrade-test.md](clean-install-upgrade-test.md).
4. Run the Windows installer production promotion repeat from a clean Windows
   profile using [launcher-production-checklist.md](launcher-production-checklist.md),
   [windows-installer-production-promotion-v0.1.2-rc3.md](windows-installer-production-promotion-v0.1.2-rc3.md),
   and [windows-installer-plan.md](windows-installer-plan.md).
5. Decide the fair launch path: continue with full disclosure, or reset once for
   a final public launch.
6. Upgrade the explorer from status-only to block, transaction, and address
   search.
7. Keep the current pool labeled as solo/test until a payout/accounting system
   exists.
8. Archive optional additional external mining reports from different networks
   and machines.
9. Invite independent node operators to join and verify the network.
