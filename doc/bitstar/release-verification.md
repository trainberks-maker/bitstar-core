# BitStar Release Verification

This document defines how BitStar release artifacts should be published and how
users should verify them before running a node, wallet, miner, or pool.

## Current Status

The `v0.x-bootstrap` releases are public bootstrap releases, not final
production releases. A production release must have signed checksums and clear
release notes before it is promoted as stable.

As of the `v0.1.1-bootstrap` bootstrap release:

- Windows launcher package exists.
- Linux x86_64 server package exists.
- SHA256 checksum files and a combined `SHA256SUMS` manifest exist for the
  published packages.
- Helper scripts exist for checksum verification and for creating/signing the
  release manifest.
- Signed `SHA256SUMS` manifest is still pending.
- Windows Authenticode code signing is still pending.

See [release-signing-policy.md](release-signing-policy.md) for release key
rules, signing workflow, and production gate requirements.
See [operator-runbook.md](operator-runbook.md) for the operator-side release
verification procedure used before installing artifacts on public seed nodes.

## Required Release Files

Every serious public release should include:

- `BitStar_Windows_<version>.zip`
- `BitStar_Linux_x86_64_<version>.tar.gz`
- `SHA256SUMS`
- `SHA256SUMS.asc`
- release notes with source commit, status, network parameters, and warnings

Optional later artifacts:

- Windows installer
- Linux arm64 package
- macOS packages
- Docker image

## Maintainer Release Steps

1. Start from a clean repository state.
2. Tag the exact source commit used for the release.
3. Build each artifact in a clean environment.
4. Create a single checksum manifest and detached signature.

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\sign-release-manifest.ps1 `
  -Artifacts ".\BitStar_Windows_v0.1.1-bootstrap.zip,.\BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz" `
  -GpgKey "<release-key-fingerprint>"
```

On Linux:

```sh
./sign-release-manifest.sh --key "<release-key-fingerprint>" \
  BitStar_Windows_v0.1.1-bootstrap.zip \
  BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz
```

5. Publish the signing key fingerprint in the release notes and website.
6. Upload artifacts, `SHA256SUMS`, `SHA256SUMS.asc`, and release notes.

Do not store release private keys, wallet files, RPC passwords, deployment
tokens, or SSH keys in this repository or in release packages.

## Operator Verification Record

Before a release is promoted on seed infrastructure, record:

- release tag
- source commit
- artifact filenames
- SHA256 values
- release signing key fingerprint
- Windows checksum verification result
- Linux checksum verification result
- GPG signature verification result
- known limitations and warnings

For bootstrap releases where `SHA256SUMS.asc` is not present yet, record the
release as checksum-verifiable only. Do not label it as a fully signed
production release.

## User Verification On Windows

Download the release package, `SHA256SUMS`, and `SHA256SUMS.asc` into the same
folder. Then verify the checksum file:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS
```

If GPG is installed and the BitStar release key is imported:

```powershell
gpg --verify .\SHA256SUMS.asc .\SHA256SUMS
```

Only run the software if both the signature and checksum verification succeed.

## User Verification On Linux

```sh
gpg --verify SHA256SUMS.asc SHA256SUMS
sh ./verify-checksums.sh SHA256SUMS
```

If the signature fails, stop. If any checksum fails, delete the artifact and
download it again from the official release page.

## Code Signing

GPG-signed checksums prove the artifact matches the release maintainer's
manifest. Windows Authenticode signing is a separate step and requires a code
signing certificate. Until that certificate exists, Windows releases must be
clearly labeled as not code-signed.

## Production Gate

BitStar should not be called production-ready until:

- the release signing key fingerprint is published;
- `SHA256SUMS` and `SHA256SUMS.asc` are published for the release;
- Windows and Linux users can verify packages with documented commands;
- the operator verification record has been completed for the exact artifacts;
- no private chain data, wallets, RPC credentials, or SSH keys are packaged;
- release notes clearly state whether the release is bootstrap, release
  candidate, or production.
