# BitStar VPS Seed Node Guide

This guide prepares a public BitStar seed node on a Linux VPS.

## Minimum VPS

- 1-2 vCPU
- 2 GB RAM recommended for compiling; 1 GB may run the node after build
- 25 GB disk minimum for early bootstrap
- Static public IPv4 address
- Ubuntu 24.04 LTS or a comparable Linux server distribution

Open only the P2P port to the internet:

- Public P2P: TCP `21333`
- Private RPC: TCP `21332` on `127.0.0.1` only

Never expose RPC port `21332` publicly.

## Build Or Install Binaries

Follow [Linux build guide](build-linux.md), then continue here after these
commands work:

```bash
bitstard -version
bitstar-cli -version
```

For the bootstrap release, Linux x86_64 binaries are also published on the
GitHub release page:

```bash
curl -L -o bitstar-linux.tar.gz \
  https://github.com/trainberks-maker/bitstar-core/releases/download/v0.1.0-bootstrap/BitStar_Linux_x86_64_v0.1.0-bootstrap.tar.gz
tar -xzf bitstar-linux.tar.gz
sudo install -m 0755 BitStar_Linux_x86_64_v0.1.0-bootstrap/bin/bitstard /usr/local/bin/bitstard
sudo install -m 0755 BitStar_Linux_x86_64_v0.1.0-bootstrap/bin/bitstar-cli /usr/local/bin/bitstar-cli
sudo install -m 0755 BitStar_Linux_x86_64_v0.1.0-bootstrap/bin/bitstar /usr/local/bin/bitstar
```

## Create Service User And Directories

```bash
sudo adduser --system --group --home /var/lib/bitstar bitstar
sudo install -d -o bitstar -g bitstar -m 0750 /var/lib/bitstar
sudo install -d -o root -g bitstar -m 0750 /etc/bitstar
```

## Configuration

Create `/etc/bitstar/bitstar.conf`:

```ini
server=1
listen=1
port=21333
rpcport=21332
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
dnsseed=0
txindex=0
printtoconsole=0
```

For the official public seed nodes, add a stable public identity and one
explicit peer:

```ini
# seed1.bitstarcoin.org
externalip=134.209.68.145:21333
addnode=seed2.bitstarcoin.org:21333
maxconnections=64
dbcache=256
```

```ini
# seed2.bitstarcoin.org
externalip=134.122.66.31:21333
addnode=seed1.bitstarcoin.org:21333
maxconnections=64
dbcache=256
```

Set permissions:

```bash
sudo chown root:bitstar /etc/bitstar/bitstar.conf
sudo chmod 0640 /etc/bitstar/bitstar.conf
```

## Install systemd Service

Copy `contrib/bitstar/bitstard.service` to systemd:

```bash
sudo cp contrib/bitstar/bitstard.service /etc/systemd/system/bitstard.service
sudo systemctl daemon-reload
sudo systemctl enable bitstard
sudo systemctl start bitstard
```

Check status:

```bash
sudo systemctl status bitstard --no-pager
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getblockhash 0
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getblockchaininfo
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getnetworkinfo
```

Expected genesis hash:

```text
00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49
```

## Firewall

If you use UFW:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 21333/tcp
sudo ufw enable
sudo ufw status
```

If your VPS provider has a cloud firewall, allow inbound TCP `21333` there too.
Keep TCP `21332` closed to the public internet.

## Public Launch Safety

For a fair no-premine launch:

- Start seed nodes from empty `/var/lib/bitstar`.
- Do not copy local test blocks or wallets to the VPS.
- Do not mine private blocks before the public launch announcement.
- Publish launch time, genesis hash, ports, source, release checksums, and node
  instructions before public mining begins.

## Official Seed Nodes

Current public seed nodes:

- `seed1.bitstarcoin.org:21333` (`134.209.68.145`), NYC1, Ubuntu 24.04 LTS
- `seed2.bitstarcoin.org:21333` (`134.122.66.31`), FRA1, Ubuntu 24.04 LTS

Seed node DNS records must stay `DNS only`, not proxied through Cloudflare,
because BitStar P2P traffic uses TCP `21333`, not HTTP/HTTPS.

As of August 21, 2026, both public seed nodes are synchronized at public block
height `1` with best block hash:

```text
00000738ca472e32ea8a6a247de802b4b2b031af610057a0c5158b12fb31b3d4
```

## Information To Record

After the node is live, record:

```bash
curl -4 https://ifconfig.me
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getblockcount
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getconnectioncount
```

Send the public IP address and node status to the release notes before adding
the node as an official seed.
