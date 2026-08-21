# BitStar Mining Guide

This guide documents local bootstrap mining commands. It is not a public mining
announcement.

## Status

The current BitStar bootstrap chain is private test data. For a fair no-premine
launch, public seed nodes should start from genesis and block 1 should be mined
publicly after the launch instructions are published.

## Create Or Load A Mining Wallet

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest createwallet miner
```

If the wallet already exists:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest loadwallet miner
```

## Generate A Mining Address

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest -rpcwallet=miner getnewaddress "" bech32
```

BitStar bech32 addresses begin with `bst1`.

## Mine Test Blocks

Replace the address with your own `bst1...` address:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest generatetoaddress 1 bst1... 50000000
```

Mine more blocks for local testing:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest generatetoaddress 100 bst1... 50000000
```

## Check Height And Balance

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest getblockcount
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest -rpcwallet=miner getbalances
```

Mining rewards mature after 100 confirmations, following Bitcoin-style coinbase
maturity behavior.

## Send A Test Transaction

Create a receiving wallet:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest createwallet user1
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest -rpcwallet=user1 getnewaddress "" bech32
```

Send using a named fee rate:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest -rpcwallet=miner -named sendtoaddress address="bst1..." amount=10 fee_rate=1
```

Mine one more block to confirm:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest generatetoaddress 1 bst1... 50000000
```

## Public Mining Requirements

Before asking the public to mine, BitStar should have:

- public source code
- public release binaries and checksums
- clean seed nodes starting from genesis
- published launch time
- published genesis hash and ports
- mining pool compatibility testing
- block explorer
- clear no-premine statement
- clear warning that mining rewards are not investment guarantees
