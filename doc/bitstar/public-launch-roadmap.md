# BitStar Public Launch Roadmap

This roadmap turns the current bootstrap into a public-ready network.

## Phase 1: Source And Bootstrap

Status: completed.

- Public GitHub repository
- BitStar Core bootstrap commit
- Windows bootstrap pre-release
- Linux x86_64 bootstrap package for seed nodes and server nodes
- Genesis verified
- Local mining verified
- Wallet transfer verified
- Two-node local sync verified

## Phase 2: Clean Public Launch Preparation

Status: in progress.

- Rebuild from clean source.
- Run a fresh 3-node rehearsal from genesis.
- Confirm no private test-chain data is packaged.
- Publish node, mining, and wallet guides.
- Publish Linux build and VPS seed node guides.
- Prepare release checksums.
- Decide exact public launch date and time.
- Prepare launch announcement with genesis hash, ports, and no-premine policy.

## Phase 3: Network Infrastructure

Status: in progress.

- Deploy at least two seed nodes on separate VPS hosts.
- Open P2P port `21333`.
- Keep RPC private.
- Add seed node addresses to the source code.
- Add DNS seed infrastructure or documented static seed peers.
- Monitor node height, peers, uptime, and forks.

Current seed nodes:

- `seed1.bitstarcoin.org:21333` (`134.209.68.145`), DNS-only Cloudflare record,
  genesis verified, RPC private.
- `seed2.bitstarcoin.org:21333` (`134.122.66.31`), DNS-only Cloudflare record,
  genesis verified, RPC private, connected to seed1.

## Phase 4: Public Tooling

- Block explorer
- Website
- Public downloads page
- Mining pool support
- Linux build guide
- Reproducible build workflow
- Release signing keys and verification guide

## Phase 5: Trust And Review

- Security review
- Legal/compliance review
- Clear risk warnings
- Public issue tracker
- Community channels
- Transparency report for no premine and launch history

## Phase 6: Exchange Or Broker Readiness

Serious exchanges usually require:

- public source code
- stable mainnet
- explorer
- wallets
- signed releases
- liquidity plan
- legal memo or compliance explanation
- active users and miners
- no hidden allocation
- clear project ownership and contact path

Code alone cannot guarantee a listing.
