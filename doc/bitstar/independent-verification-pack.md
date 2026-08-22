# BitStar Independent Verification Pack

This pack is for an independent tester who wants to verify BitStar release
artifacts and network behavior without relying on maintainer claims.

Current target release: `v0.1.2-rc2`

Release URL:
`https://github.com/trainberks-maker/bitstar-core/releases/tag/v0.1.2-rc2`

Release key fingerprint:
`5744BDF701AFDCF43983AB96B87F9907D27EC983`

Genesis hash:
`00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`

## Scope

An independent verification should confirm:

- the public release key imports successfully;
- the signed checksum manifest verifies with the expected release key;
- the downloaded Windows or Linux artifact matches the published SHA256;
- a clean node starts from an empty datadir;
- the node reports the expected genesis hash;
- the node connects to public seed nodes;
- the node reaches the public chain tip or progresses toward it;
- the tester records the exact commands and result.

This pack does not ask testers to trust a maintainer wallet, RPC password,
private seed, SSH key, or existing data directory. Always use a clean temporary
datadir for this verification.

## Files To Download

Download these files from the release page into one folder:

- `bitstar-release-key.asc`
- `SHA256SUMS-v0.1.2-rc2`
- `SHA256SUMS-v0.1.2-rc2.asc`
- `verify-checksums.ps1`
- `verify-checksums.sh`
- one or both release packages:
  - `BitStar_Windows_v0.1.2-rc2.zip`
  - `BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz`

Expected SHA256 values:

```text
416c5232a7155ba85fcdfd1b4005bf184d75055433193b214cf8d7a1cf57dd46  BitStar_Windows_v0.1.2-rc2.zip
a13e9ec2c13a97f169f6d9e3c37256c27caa878dbe08d9a971da2be05f774392  BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz
```

## Windows Verification

Run these commands from the folder containing the downloaded release files:

```powershell
gpg --import .\bitstar-release-key.asc
gpg --fingerprint "BitStar Release"
gpg --verify .\SHA256SUMS-v0.1.2-rc2.asc .\SHA256SUMS-v0.1.2-rc2
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS-v0.1.2-rc2
```

The fingerprint shown by GPG must include:

```text
5744BDF701AFDCF43983AB96B87F9907D27EC983
```

Extract `BitStar_Windows_v0.1.2-rc2.zip` into a new folder and start a clean
node with a temporary datadir:

```powershell
$Stamp = Get-Date -Format yyyyMMddHHmmss
$Release = Join-Path $env:TEMP "bitstar-release-rc2-$Stamp"
$DataDir = Join-Path $env:TEMP "bitstar-independent-rc2-$Stamp"
Expand-Archive -Path .\BitStar_Windows_v0.1.2-rc2.zip -DestinationPath $Release
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
& "$Release\bitstard.exe" -datadir="$DataDir" -server=1 -listen=1 `
  -addnode=seed1.bitstarcoin.org:21333 `
  -addnode=seed2.bitstarcoin.org:21333
```

In another terminal, verify the running node:

```powershell
& "$Release\bitstar-cli.exe" -datadir="$DataDir" getblockhash 0
& "$Release\bitstar-cli.exe" -datadir="$DataDir" getblockchaininfo
& "$Release\bitstar-cli.exe" -datadir="$DataDir" getconnectioncount
& "$Release\bitstar-cli.exe" -datadir="$DataDir" stop
```

Pass conditions:

- `getblockhash 0` equals the BitStar genesis hash;
- `getblockchaininfo` reports chain `main`;
- block count increases or reaches the public explorer height;
- `initialblockdownload` eventually becomes `false`;
- connection count is at least `1`;
- the node stops cleanly.

## Linux Verification

Run these commands from the folder containing the downloaded release files:

```sh
gpg --import bitstar-release-key.asc
gpg --fingerprint "BitStar Release"
gpg --verify SHA256SUMS-v0.1.2-rc2.asc SHA256SUMS-v0.1.2-rc2
sh ./verify-checksums.sh SHA256SUMS-v0.1.2-rc2
```

Extract and start a clean node:

```sh
tar -xzf BitStar_Linux_x86_64_v0.1.2-rc2.tar.gz
export RELEASE="$PWD/BitStar_Linux_x86_64_v0.1.2-rc2"
export DATADIR="/tmp/bitstar-independent-rc2"
mkdir -p "$DATADIR"
"$RELEASE/bin/bitstard" -datadir="$DATADIR" -server=1 -listen=1 \
  -addnode=seed1.bitstarcoin.org:21333 \
  -addnode=seed2.bitstarcoin.org:21333 -daemon
```

Verify the node:

```sh
"$RELEASE/bin/bitstar-cli" -datadir="$DATADIR" getblockhash 0
"$RELEASE/bin/bitstar-cli" -datadir="$DATADIR" getblockchaininfo
"$RELEASE/bin/bitstar-cli" -datadir="$DATADIR" getconnectioncount
"$RELEASE/bin/bitstar-cli" -datadir="$DATADIR" stop
```

Pass conditions are the same as Windows.

## Optional Upgrade Repeat

This optional test repeats the maintainer upgrade smoke test using a clean
temporary datadir:

1. Start `v0.1.1-bootstrap` with a temporary datadir.
2. Verify genesis, block height, best block, and connection count.
3. Stop `v0.1.1-bootstrap` cleanly.
4. Start `v0.1.2-rc2` with the same datadir.
5. Confirm the new release opens the existing block database without reindex,
   reaches the same height or higher, keeps the same genesis hash, and stops
   cleanly.

Do not use a wallet containing real funds for this test.

## Result Template

Independent testers should publish a short result using this template:

```text
BitStar independent verification

Tester:
Date UTC:
Platform:
Release tag: v0.1.2-rc2
Release URL: https://github.com/trainberks-maker/bitstar-core/releases/tag/v0.1.2-rc2
Release key fingerprint observed:
GPG manifest verification: PASS/FAIL
Checksum verification: PASS/FAIL
Artifact tested:
Clean datadir:
Genesis hash:
Block height:
Best block:
Connection count:
Initial block download:
Upgrade repeat performed: yes/no
Result: PASS/FAIL
Notes:
```

Good places to publish the result:

- a GitHub issue using the
  [independent verification report template](https://github.com/trainberks-maker/bitstar-core/issues/new?template=independent_verification.yml);
- a pull request adding the result to
  [clean-install-upgrade-test.md](clean-install-upgrade-test.md);
- a public post that links back to the release and includes the exact commands.

## Failure Handling

If any verification step fails:

1. Stop the node if it is running.
2. Do not mine or receive funds with that package.
3. Delete the downloaded artifacts.
4. Download again from the official release page.
5. If the failure repeats, open a GitHub issue with the exact command output.

BitStar should not be called production-ready until at least one independent
verification result has been published and reviewed.
