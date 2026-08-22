# BitStar Release Checklist

This checklist must be completed before BitStar is presented as a production
release.

## Release Labels

Use clear labels so users know the risk level:

- `v0.x-bootstrap`: public test / bootstrap release
- `v0.x-rcN`: release candidate
- `v1.0.0-mainnet`: first production mainnet release, only after all gates pass

Do not call a release production-ready while the pre-release warning is still
present in the node software.

## Source Preparation

- choose the exact Git commit for the release
- tag the commit
- confirm `git status` is clean
- document all BitStar-specific changes from upstream Bitcoin Core
- verify project constants:
  - name: BitStar
  - ticker: BST
  - max supply: 21,000,000 BST
  - target block time: 10 minutes
  - halving interval: 210,000 blocks
  - initial subsidy: 50 BST
  - P2P port: 21333
  - RPC port: 21332
  - bech32 prefix: bst
  - genesis hash: `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`

## Build Matrix

Required artifacts for a serious public release:

- Windows x86_64 zip
- Windows x86_64 installer, if GUI packaging is ready
- Linux x86_64 tar.gz
- Linux arm64 tar.gz, recommended for VPS and single-board nodes
- source archive from GitHub tag

Optional later artifacts:

- macOS x86_64
- macOS arm64
- Docker image for node operators

## Clean Build Checks

- build in a clean environment
- run unit tests
- run selected functional tests
- start a fresh node from empty datadir
- verify genesis block
- verify the node connects to seed1 and seed2
- verify wallet creation, address generation, backup, and restore
- verify `getblocktemplate '{"rules":["segwit"]}'`
- verify `submitblock` on a private test network
- run the public infrastructure checks in
  [operator-runbook.md](operator-runbook.md) before installing the release on
  seed nodes
- confirm no private wallets, chain data, RPC credentials, or SSH keys are
  packaged

## Signing And Verification

- create a dedicated release signing key
- publish the signing key fingerprint
- publish SHA256 checksums for every artifact
- sign the checksum file or release manifest
- use `contrib/bitstar/release/sign-release-manifest.ps1` or
  `contrib/bitstar/release/sign-release-manifest.sh` to create `SHA256SUMS`
  and `SHA256SUMS.asc`
- document verification commands for Windows and Linux users
- keep [release-verification.md](release-verification.md) current for every
  public release
- keep [release-signing-policy.md](release-signing-policy.md) current when
  release key ownership changes
- keep [operator-runbook.md](operator-runbook.md) current when seed, explorer,
  pool, or backup operations change
- keep private signing keys offline
- label Windows builds as not code-signed until an Authenticode certificate is
  available

## Release Notes

Release notes must include:

- release name and version
- source commit
- status: bootstrap, release candidate, or production
- network parameters
- seed nodes
- explorer URL
- mining instructions
- known limitations
- wallet safety warning
- no exchange/listing/profit promises
- signing key fingerprint and checksum verification instructions

## Final Launch Checklist

Before a final production launch:

- decide whether to continue current bootstrap chain or perform final reset
- publish the launch decision publicly
- publish release artifacts and checksums before public mining starts
- publish exact launch date and time in UTC
- keep seed nodes online and synced
- run `bitstar-operator-status` on each seed or pool host and archive the
  operator verification notes
- verify explorer follows the same best block as seed1 and seed2
- verify pool/test endpoint status is correctly labeled
- archive the launch announcement
