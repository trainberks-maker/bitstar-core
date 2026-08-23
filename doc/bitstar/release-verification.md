# BitStar Release Verification

This document defines how BitStar release artifacts should be published and how
users should verify them before running a node, wallet, miner, or pool.

## Current Status

The `v0.x-bootstrap` and `v0.x-rcN` releases are public bootstrap or release
candidate releases, not final production releases. A production release must
have signed checksums, clean test records, independent verification, and clear
release notes before it is promoted as stable.

As of the `v0.1.2-rc3` release candidate:

- Windows launcher package exists.
- Windows installer artifact exists and is published as unsigned pre-release
  software.
- Linux x86_64 server package exists for `v0.1.2-rc3`.
- SHA256 checksum files and a combined `SHA256SUMS-v0.1.2-rc3` manifest exist
  for the Windows package, Windows installer, and Linux x86_64 package.
- Helper scripts exist for checksum verification and for creating/signing the
  release manifest.
- Helper scripts exist for exporting only the public release key.
- Signed `SHA256SUMS-v0.1.2-rc3.asc` manifest is published.
- Public release key `bitstar-release-key.asc` is published.
- Release key fingerprint:
  `5744BDF701AFDCF43983AB96B87F9907D27EC983`
- The release readiness gate passes with:
  `Result: release artifacts are signed and checksum verified.`
- Windows launcher clean smoke test passed.
- Windows installer silent install/uninstall smoke test passed.
- Linux x86_64 `v0.1.2-rc3` clean temporary-datadir smoke test passed.
- Windows and Linux synthetic upgrade smoke tests from `v0.1.1-bootstrap` to
  `v0.1.2-rc2` passed; the `v0.1.2-rc3` Windows installer gate passed, while
  a Linux `v0.1.2-rc3` upgrade repeat still needs to be archived.
- External Windows verification report #1 passed and is accepted as closing
  the `v0.1.2-rc3` external Windows tester gate.
- External mining/pool smoke verification passed for share acceptance against
  `pool.bitstarcoin.org:3333`; this does not certify a production payout pool.
- Windows Authenticode code signing is still pending.

See [release-signing-policy.md](release-signing-policy.md) for release key
rules, signing workflow, and production gate requirements.
See [release-key-ceremony.md](release-key-ceremony.md) for creating and backing
up the dedicated release signing key safely.
See [release-package-audit.md](release-package-audit.md) for checking that
release archives do not contain wallet data, private keys, or credentials.
See [clean-install-upgrade-test.md](clean-install-upgrade-test.md) for the
clean install, launcher, and upgrade test record required before a release
candidate or final production release.
See [independent-verification-pack.md](independent-verification-pack.md) for
the exact checklist an outside tester can run and publish.
See [external-windows-tester-gate-v0.1.2-rc3.md](external-windows-tester-gate-v0.1.2-rc3.md)
for the closed external Windows tester gate.
See [external-mining-pool-verification-v0.1.2-rc3.md](external-mining-pool-verification-v0.1.2-rc3.md)
for the external mining/pool share-acceptance smoke record.
See [windows-installer-production-promotion-v0.1.2-rc3.md](windows-installer-production-promotion-v0.1.2-rc3.md)
for the clean-profile Windows installer repeat required before installer
promotion.
See [operator-runbook.md](operator-runbook.md) for the operator-side release
verification procedure used before installing artifacts on public seed nodes.
See [launcher-production-checklist.md](launcher-production-checklist.md) and
[windows-installer-plan.md](windows-installer-plan.md) before publishing a
Windows installer.

## Required Release Files

Every serious public release should include:

- `BitStar_Windows_<version>.zip`
- `BitStar_Core_Setup_<version>.exe`, if the Windows launcher installer gate
  is complete enough for pre-release testing
- `BitStar_Linux_x86_64_<version>.tar.gz`
- versioned checksum manifest, for example `SHA256SUMS-v0.1.2-rc3`
- detached manifest signature, for example `SHA256SUMS-v0.1.2-rc3.asc`
- `bitstar-release-key.asc`
- release notes with source commit, status, network parameters, and warnings

Optional later artifacts:

- Linux arm64 package
- macOS packages
- Docker image

## Maintainer Release Steps

1. Start from a clean repository state.
2. Tag the exact source commit used for the release.
3. Build each artifact in a clean environment.
4. Run the release package hygiene audit.
5. If publishing a Windows installer, build it from the verified Windows
   package and run the clean installer test before creating the manifest.
6. Create a single checksum manifest and detached signature.

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\sign-release-manifest.ps1 `
  -Artifacts ".\BitStar_Windows_v0.1.2-rc3.zip,.\BitStar_Core_Setup_v0.1.2-rc3.exe,.\BitStar_Linux_x86_64_v0.1.2-rc3.tar.gz" `
  -Output ".\SHA256SUMS-v0.1.2-rc3" `
  -GpgKey "<release-key-fingerprint>"
```

On Linux:

```sh
./sign-release-manifest.sh --output SHA256SUMS-v0.1.2-rc3 --key "<release-key-fingerprint>" \
  BitStar_Windows_v0.1.2-rc3.zip \
  BitStar_Core_Setup_v0.1.2-rc3.exe \
  BitStar_Linux_x86_64_v0.1.2-rc3.tar.gz
```

7. Export `bitstar-release-key.asc` with the public-key helper.
8. Publish the signing key fingerprint in the release notes and website.
9. Run the release readiness gate.

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\check-release-readiness.ps1 `
  -ReleaseDir .\ `
  -Manifest "SHA256SUMS-v0.1.2-rc3"
```

On Linux:

```sh
./check-release-readiness.sh --release-dir . --manifest SHA256SUMS-v0.1.2-rc3
```

10. Upload artifacts, the versioned `SHA256SUMS-v0.1.2-rc3` manifest,
   `SHA256SUMS-v0.1.2-rc3.asc`, public release key, verification scripts, and
   release notes.

Do not store release private keys, wallet files, RPC passwords, deployment
tokens, or SSH keys in this repository or in release packages.

## Operator Verification Record

Before a release is promoted on seed infrastructure, record:

- release tag
- source commit
- artifact filenames
- SHA256 values
- release signing key fingerprint
- release readiness gate result
- release package hygiene scan result
- clean install test result
- upgrade test result
- Windows launcher smoke test result
- Windows checksum verification result
- Linux checksum verification result
- GPG signature verification result
- independent verification result
- known limitations and warnings

For older bootstrap releases where a detached manifest signature is not
present, record the release as checksum-verifiable only. For
`v0.1.1-bootstrap`, `v0.1.2-rc2`, and `v0.1.2-rc3`, record them as signed
pre-releases. Do not label any bootstrap or release candidate build as a final
production release.

## User Verification On Windows

For the current release candidate, download the release package,
`SHA256SUMS-v0.1.2-rc3`, `SHA256SUMS-v0.1.2-rc3.asc`, and
`bitstar-release-key.asc` into the same folder. Import the public key, verify
the signature, then verify the checksum file:

```powershell
gpg --import .\bitstar-release-key.asc
gpg --verify .\SHA256SUMS-v0.1.2-rc3.asc .\SHA256SUMS-v0.1.2-rc3
```

```powershell
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS-v0.1.2-rc3
```

Only run the software if both the signature and checksum verification succeed.

## User Verification On Linux

```sh
gpg --import bitstar-release-key.asc
gpg --verify SHA256SUMS-v0.1.2-rc3.asc SHA256SUMS-v0.1.2-rc3
sh ./verify-checksums.sh SHA256SUMS-v0.1.2-rc3
tar -xzf BitStar_Linux_x86_64_v0.1.2-rc3.tar.gz
cd BitStar_Linux_x86_64_v0.1.2-rc3
./bin/bitstard -version
```

If the signature fails, stop. If any checksum fails, delete the artifact and
download it again from the official release page.

## Code Signing

GPG-signed checksums prove the artifact matches the release maintainer's
manifest. Windows Authenticode signing is a separate step and requires a code
signing certificate. Until that certificate exists, Windows zip and installer
releases must be clearly labeled as not code-signed.

## Production Gate

BitStar should not be called production-ready until:

- the release signing key fingerprint is published;
- `bitstar-release-key.asc` is published for the release;
- a signed checksum manifest is published for the release;
- the release readiness gate passes without unsigned-bootstrap mode;
- Windows and Linux users can verify packages with documented commands;
- the operator verification record has been completed for the exact artifacts;
- at least one independent tester has published a verification result using
  [independent-verification-pack.md](independent-verification-pack.md);
- no private chain data, wallets, RPC credentials, or SSH keys are packaged;
- release notes clearly state whether the release is bootstrap, release
  candidate, or production.
