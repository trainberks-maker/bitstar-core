# BitStar Release Signing Policy

This policy defines how BitStar release artifacts are signed and verified.
For the safe key creation procedure, see
[release-key-ceremony.md](release-key-ceremony.md).

## Goal

Users must be able to prove that downloaded BitStar release packages match the
manifest published by the project maintainer.

For the bootstrap stage, the minimum acceptable release verification stack is:

- one `SHA256SUMS` file covering all release packages;
- one detached GPG signature, `SHA256SUMS.asc`;
- a published release signing key fingerprint;
- the public release key, `bitstar-release-key.asc`;
- verification commands for Windows and Linux.

Windows Authenticode signing is a separate requirement and should be added when
the project has a code-signing certificate. Until then, Windows packages must be
clearly labeled as not Authenticode-signed.

## Key Rules

- Use a dedicated BitStar release signing key.
- Keep the private key offline or on a dedicated maintainer machine.
- Do not store the private key, passphrase, wallet files, RPC passwords, SSH
  keys, or deployment tokens in the repository.
- Publish only the public key and fingerprint.
- Rotate the key publicly if it is lost, exposed, or transferred to another
  maintainer.
- Never publish a production release without signed checksums.

## Maintainer Workflow

1. Build the release packages from the tagged source commit.
2. Put all release packages in one clean release folder.
3. Create and sign the manifest on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\sign-release-manifest.ps1 `
  -Artifacts ".\BitStar_Windows_v0.1.1-bootstrap.zip,.\BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz" `
  -GpgKey "<release-key-fingerprint>"
```

Or on Linux:

```sh
./sign-release-manifest.sh --key "<release-key-fingerprint>" \
  BitStar_Windows_v0.1.1-bootstrap.zip \
  BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz
```

4. Confirm the signature:

```sh
gpg --verify SHA256SUMS.asc SHA256SUMS
```

5. Run the release readiness gate.

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\check-release-readiness.ps1 -ReleaseDir .\
```

On Linux:

```sh
./check-release-readiness.sh --release-dir .
```

The result must say:

```text
Result: release artifacts are signed and checksum verified.
```

6. Export the public release key:

```powershell
powershell -ExecutionPolicy Bypass -File .\export-release-public-key.ps1 -GpgKey "<release-key-fingerprint>"
```

or:

```sh
./export-release-public-key.sh --key "<release-key-fingerprint>"
```

7. Upload the packages, `SHA256SUMS`, `SHA256SUMS.asc`,
   `bitstar-release-key.asc`, verification scripts, and release notes to the
   GitHub release.

## User Verification

Users should verify the GPG signature first, then verify package checksums.

On Windows:

```powershell
gpg --import .\bitstar-release-key.asc
gpg --verify .\SHA256SUMS.asc .\SHA256SUMS
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS
```

On Linux:

```sh
gpg --import bitstar-release-key.asc
gpg --verify SHA256SUMS.asc SHA256SUMS
./verify-checksums.sh SHA256SUMS
```

If the signature fails, stop. If any checksum fails, delete the package and
download it again from the official release page.

## Production Gate

BitStar release engineering is not production-ready until:

- the public signing key fingerprint is listed in release notes and on the
  website;
- `bitstar-release-key.asc` is published for the current release;
- `SHA256SUMS.asc` is published for the current release;
- `check-release-readiness.ps1` or `check-release-readiness.sh` passes without
  `--allow-unsigned-bootstrap`;
- clean verification succeeds on both Windows and Linux;
- at least one independent person can reproduce or verify the release package
  checksums.
