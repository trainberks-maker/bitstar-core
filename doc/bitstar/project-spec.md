# BitStar Project Spec

## Core Parameters

- Name: BitStar
- Ticker: BST
- Base: Bitcoin Core fork
- Consensus: Proof-of-Work, SHA256d
- Max money: 21,000,000 BST
- Initial block subsidy: 50 BST
- Halving interval: 210,000 blocks
- Target block time: 10 minutes
- Difficulty retarget: 2,016 blocks
- Premine: none

## Genesis Block

- Timestamp text: `BitStar 21/Aug/2026 fair launch - no premine - 21 million BST`
- Unix time: `1787270400`
- Bits: `0x1e0ffff0`
- Nonce: `1415949`
- Merkle root: `0da084d5ea9a6e47f672ef25d0ac3fe1cf9434e232a9ce38d8566ab4619072fa`
- Genesis hash: `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`
- PoW limit: `00000ffff0000000000000000000000000000000000000000000000000000000`

## Network Parameters

- Mainnet P2P port: `21333`
- Mainnet RPC port: `21332`
- Message start bytes: `ba 57 0b 51`
- Bech32 HRP: `bst`
- P2PKH version byte: `25`
- P2SH version byte: `85`
- WIF secret key byte: `153`
- Config file: `bitstar.conf`
- Windows data directory: `%LOCALAPPDATA%\BitStar`
- macOS data directory: `~/Library/Application Support/BitStar`
- Linux data directory: `~/.bitstar`

## Bootstrap Scope

- Replaced mainnet genesis, message bytes, ports, address prefixes, data
  directory, config filename, client name, P2P user agent, and GUI unit labels.
- Kept the Bitcoin-style 21M supply schedule, 10-minute blocks, 210,000-block
  halvings, and no-premine design.
- Renamed primary Windows binaries to `bitstard.exe`, `bitstar-cli.exe`,
  `bitstar-util.exe`, and `bitstar.exe`.
- Added a reproducible genesis helper at `contrib/devtools/bitstar_genesis.py`.

## Next Milestones

1. Review BIP activation heights and chain-assumption behavior.
2. Rebuild clean binaries from source and repeat local validation.
3. Add public seed nodes and DNS seed infrastructure.
4. Publish signed releases and checksums.
5. Prepare explorer, website, mining guide, node guide, and wallet guide.
6. Complete legal and compliance review before any broker or exchange approach.
