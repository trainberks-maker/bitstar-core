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

## Information To Record

After the node is live, record:

```bash
curl -4 https://ifconfig.me
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getblockcount
sudo -u bitstar bitstar-cli -datadir=/var/lib/bitstar getconnectioncount
```

Send the public IP address and node status to the release notes before adding
the node as an official seed.

