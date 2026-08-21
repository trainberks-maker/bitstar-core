# BitStar Linux Build Guide

This guide builds headless BitStar Core binaries for a Linux VPS or server.
For seed nodes, the GUI and wallet are not required.

## Target

- OS: Ubuntu 24.04 LTS or another current Linux distribution
- Architecture: x86_64
- Binaries: `bitstard`, `bitstar-cli`
- Purpose: public seed node or server-side validation node

## Install Build Tools

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y git curl build-essential cmake python3 libboost-dev
```

If you also want wallet support, install SQLite and remove
`-DENABLE_WALLET=OFF` from the CMake command below:

```bash
sudo apt install -y libsqlite3-dev
```

## Clone Source

```bash
git clone https://github.com/BitStarCoin/bitstar-core.git
cd bitstar-core
```

## Configure A Seed-Node Build

```bash
cmake -B build \
  -DBUILD_GUI=OFF \
  -DENABLE_IPC=OFF \
  -DENABLE_WALLET=OFF \
  -DBUILD_TESTS=OFF \
  -DBUILD_BENCH=OFF
```

## Build

Use `-j2` on small VPS machines. Increase it only if the server has enough RAM.
The internal CMake target names still use upstream names, but the generated
executables are BitStar-branded.

```bash
cmake --build build --target bitcoind bitcoin-cli -j2
```

The output files should be:

```text
build/bin/bitstard
build/bin/bitstar-cli
```

Install them:

```bash
sudo install -m 0755 build/bin/bitstard /usr/local/bin/bitstard
sudo install -m 0755 build/bin/bitstar-cli /usr/local/bin/bitstar-cli
```

Verify:

```bash
bitstard -version
bitstar-cli -version
```

## Important

Do not copy a local Windows data directory, wallet directory, or private test
chain onto a public seed node. Public seed nodes for a no-premine launch must
start from a clean data directory.
