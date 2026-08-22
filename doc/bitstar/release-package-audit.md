# BitStar Release Package Audit

This document defines the minimum package hygiene audit before BitStar release
archives are published.

The audit checks for high-risk mistakes, such as accidentally packaging wallet
files, local chain data, SSH keys, RPC credentials, or deployment tokens. It is
not a replacement for code review, reproducible builds, or an external security
audit.

## Required Command

Run the package scan against the exact artifacts that will be uploaded.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scan-release-package.ps1 `
  -ReleaseDir . `
  -Artifacts "BitStar_Windows_v0.1.1-bootstrap.zip,BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz"
```

Linux:

```sh
./scan-release-package.sh --release-dir . \
  --artifact BitStar_Windows_v0.1.1-bootstrap.zip \
  --artifact BitStar_Linux_x86_64_v0.1.1-bootstrap.tar.gz
```

The result must be:

```text
Result: package hygiene scan passed.
```

## Files That Must Never Be Packaged

- wallet databases such as `wallet.dat`
- `wallets/`
- `blocks/`
- `chainstate/`
- `indexes/`
- `peers.dat`
- `mempool.dat`
- `.cookie`
- `.ssh/`
- SSH private keys such as `id_rsa` or `id_ed25519`
- private key files such as `.pem`, `.p12`, or `.pfx`

## Config Rules

Release examples may include safe local configuration, such as:

```text
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
```

Release packages must not include:

```text
rpcbind=0.0.0.0
rpcallowip=0.0.0.0/0
rpcpassword=<real-password>
rpcauth=<real-auth-secret>
```

## Production Gate

Do not publish a production release if the package hygiene scan fails. Fix the
package source, rebuild the artifacts, regenerate checksums, sign the new
manifest, and run release readiness again.
