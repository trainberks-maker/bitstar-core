# BitStar Release Key Ceremony

This document defines the safe procedure for creating and using the BitStar
release signing key. The private key is a project trust root. Treat it with the
same care as production infrastructure credentials.

## Safety Rules

- Create the release key on the maintainer machine that will sign releases.
- Use a dedicated BitStar release key, not a personal everyday key.
- Protect the key with a strong passphrase.
- Never paste the private key, passphrase, wallet files, SSH private keys, RPC
  passwords, deployment tokens, or API tokens into chat, GitHub issues,
  documentation, release notes, or the repository.
- Publish only the public key and fingerprint.
- Keep an encrypted offline backup of the secret key and revocation certificate.

## Required Tools

Windows maintainers should install Gpg4win. Linux maintainers should install
GnuPG from the operating system package manager. On Windows, Git for Windows
also includes GPG and the BitStar PowerShell release scripts will try to find it
automatically.

Check that GPG is available:

```powershell
gpg --version
```

If normal PowerShell cannot find `gpg`, try the Git for Windows GPG path:

```powershell
& "C:\Program Files\Git\usr\bin\gpg.exe" --version
```

or:

```sh
gpg --version
```

## Create The Release Signing Key

Run this on the maintainer machine:

Windows with Git for Windows GPG:

```powershell
& "C:\Program Files\Git\usr\bin\gpg.exe" --quick-generate-key "BitStar Release <release@bitstarcoin.org>" ed25519 sign 2y
```

Linux, macOS, or Windows where `gpg` is already in `PATH`:

```sh
gpg --quick-generate-key "BitStar Release <release@bitstarcoin.org>" ed25519 sign 2y
```

GPG will ask for a passphrase. Use a strong passphrase and do not share it.

Then list the key and copy the full fingerprint:

Windows with Git for Windows GPG:

```powershell
& "C:\Program Files\Git\usr\bin\gpg.exe" --list-secret-keys --keyid-format LONG "BitStar Release"
```

Linux, macOS, or Windows where `gpg` is already in `PATH`:

```sh
gpg --list-secret-keys --keyid-format LONG "BitStar Release"
```

Record the fingerprint in:

- release notes
- `doc/bitstar/release-verification.md`
- the official website release section

## Export Public Key

Export only the public key:

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\export-release-public-key.ps1 -GpgKey "<release-key-fingerprint>"
```

Linux:

```sh
./export-release-public-key.sh --key "<release-key-fingerprint>"
```

The public key may be committed or uploaded to a release. The secret key must
never be committed.

## Backup Secret Key Offline

Export the secret key only for encrypted offline backup:

```sh
gpg --armor --export-secret-keys <release-key-fingerprint> > bitstar-release-secret-key-OFFLINE.asc
```

Immediately move this file to encrypted offline storage, then delete the working
copy from the normal downloads/release folder.

Create a revocation certificate and store it offline:

```sh
gpg --output bitstar-release-revocation-OFFLINE.asc --gen-revoke <release-key-fingerprint>
```

## Sign A Release Manifest

Put all release artifacts and the signing helper scripts in one clean release
folder. From that folder, run one of the following commands.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\sign-release-manifest.ps1 `
  -Artifacts ".\BitStar_Windows_v0.1.2-rc2.zip,.\BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz" `
  -Output ".\SHA256SUMS-v0.1.2-rc2" `
  -GpgKey "<release-key-fingerprint>"
```

Linux:

```sh
./sign-release-manifest.sh --output SHA256SUMS-v0.1.2-rc2 --key "<release-key-fingerprint>" \
  BitStar_Windows_v0.1.2-rc2.zip \
  BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz
```

Expected outputs:

- `SHA256SUMS-v0.1.2-rc2`
- `SHA256SUMS-v0.1.2-rc2.asc`
- `bitstar-release-key.asc`, created by the public-key export helper

## Verify Before Publishing

Verify the detached signature:

```sh
gpg --verify SHA256SUMS-v0.1.2-rc2.asc SHA256SUMS-v0.1.2-rc2
```

Run the release readiness gate.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\check-release-readiness.ps1 `
  -ReleaseDir .\ `
  -Manifest "SHA256SUMS-v0.1.2-rc2"
```

Linux:

```sh
./check-release-readiness.sh --release-dir . --manifest SHA256SUMS-v0.1.2-rc2
```

The result must be:

```text
Result: release artifacts are signed and checksum verified.
```

If the result says `bootstrap-verifiable only` or `not production-ready`, do not
promote the release as production.

## Publish

Upload these public files:

- release artifacts
- versioned checksum manifest, for example `SHA256SUMS-v0.1.2-rc2`
- detached manifest signature, for example `SHA256SUMS-v0.1.2-rc2.asc`
- `bitstar-release-key.asc`
- release notes
- verification scripts

Never upload:

- secret release key
- key passphrase
- wallet files
- RPC credentials
- SSH private keys
- deployment tokens
