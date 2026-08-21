# BitStar Windows Build Guide

This guide documents the local Windows build path used for the bootstrap
binaries.

## Tested Toolchain

- Windows 11
- Visual Studio 2026 Community
- CMake `4.4.2`
- Visual Studio bundled vcpkg
- Boost and SQLite from vcpkg

## Configure

Run from the source directory:

```cmd
cmd /c ""C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" && set VCPKG_ROOT=C:\Program Files\Microsoft Visual Studio\18\Community\VC\vcpkg&& "C:\Program Files\CMake\bin\cmake.exe" -B build --preset vs2026 -DVCPKG_MANIFEST_NO_DEFAULT_FEATURES=ON -DVCPKG_MANIFEST_FEATURES=wallet -DVCPKG_INSTALLED_DIR="C:\Users\bajra\Documents\Codex\2026-08-21\https-github-com-bitcoin-bitcoin-https\work\vcpkg_installed" -DBUILD_GUI=OFF -DWITH_ZMQ=OFF -DENABLE_IPC=OFF -DBUILD_TESTS=OFF -DBUILD_BENCH=OFF -DBUILD_FUZZ_BINARY=OFF -DBUILD_UTIL=ON -DBUILD_TX=OFF -DBUILD_WALLET_TOOL=OFF -DBUILD_UTIL_CHAINSTATE=OFF -DCMAKE_COMPILE_WARNING_AS_ERROR=OFF"
```

Expected configure summary should include:

```text
bitstar ............................. ON
bitstard ............................ ON
bitstar-cli ......................... ON
bitstar-util ........................ ON
wallet support ...................... ON
```

## Build

```cmd
cmd /c ""C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files\CMake\bin\cmake.exe" --build build --config Release --target bitcoind bitcoin-cli bitcoin-util bitcoin -j 6"
```

Expected binaries:

```text
build\bin\Release\bitstard.exe
build\bin\Release\bitstar-cli.exe
build\bin\Release\bitstar-util.exe
build\bin\Release\bitstar.exe
build\bin\Release\sqlite3.dll
```

## Quick Verification

```cmd
build\bin\Release\bitstard.exe -version
build\bin\Release\bitstar-cli.exe -help
build\bin\Release\bitstar-util.exe getchainparams
```

Expected genesis hash:

```text
00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49
```

Expected BitStar parameters from `getchainparams`:

```text
target_spacing: 600
default_port: 21333
magic: ba570b51
bech32_hrp: bst
```

## Public Release Warning

The existing local chain through height `181` is test data. Do not package
wallet files or `%LOCALAPPDATA%\BitStar` chain data into a public no-premine
release.
