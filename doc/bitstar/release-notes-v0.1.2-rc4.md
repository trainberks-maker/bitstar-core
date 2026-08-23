# BitStar Core v0.1.2-rc4 Release Notes

BitStar Core `v0.1.2-rc4` is a Windows release-candidate refresh for the
launcher and installer production gate.

This is still unsigned pre-release software. Use it for public testing,
independent verification, node operation, wallet backup tests, and pool/mining
smoke tests. Do not treat this release candidate as a final production wallet
or merchant release.

## Why rc4 Exists

External Windows testing of `v0.1.2-rc3` found that launcher option `3`
could fail when the `wallet1` directory already existed but was not currently
loaded by the node.

`v0.1.2-rc4` rebuilds the Windows zip and Windows installer with the fixed
launcher flow.

## Windows Launcher Changes

- Option `3` now creates or loads `wallet1`, prints a mining address, and saves
  it to the user's Desktop as `bitstar-address.txt`.
- Option `4` now loads `wallet1` before backing up the wallet when no wallet is
  already loaded.
- Option `5` now clearly warns when `bitstar-qt.exe` is not included in the
  package. The current Windows package is node and CLI-wallet only.

## Release Artifacts

- `BitStar_Windows_v0.1.2-rc4.zip`
- `BitStar_Core_Setup_v0.1.2-rc4.exe`
- `SHA256SUMS-v0.1.2-rc4`
- `SHA256SUMS-v0.1.2-rc4.asc`
- `bitstar-release-key.asc`
- `verify-checksums.ps1`

## SHA256

```text
faf40eb65f79784d7f754bbdf586bece9726af99e6c72cb6148a7a750f91acc3  BitStar_Windows_v0.1.2-rc4.zip
e05884a921dff55dbb0a0e865b3311a38ae322bf20b4eb8e290c11a9cc2a2397  BitStar_Core_Setup_v0.1.2-rc4.exe
```

## Signing Key

Release key fingerprint:

```text
5744BDF701AFDCF43983AB96B87F9907D27EC983
```

## Verification

On Windows, from the folder containing the downloaded files:

```powershell
gpg --import .\bitstar-release-key.asc
gpg --verify .\SHA256SUMS-v0.1.2-rc4.asc .\SHA256SUMS-v0.1.2-rc4
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS-v0.1.2-rc4
```

If GPG is not installed, at least check the Windows artifact hash:

```powershell
Get-FileHash .\BitStar_Windows_v0.1.2-rc4.zip -Algorithm SHA256
Get-FileHash .\BitStar_Core_Setup_v0.1.2-rc4.exe -Algorithm SHA256
```

## Known Limits

- Windows Authenticode signing is not available yet.
- No graphical `bitstar-qt.exe` wallet is included yet.
- The public pool is still a solo/test pool, not a full payout dashboard pool.
- This release still needs the dedicated clean-profile Windows installer
  production repeat before any stable/production label.
