#!/usr/bin/env python3
import json
import os
import subprocess
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "0.0.0.0"
PORT = 8090
CLI = ["/usr/local/bin/bitstar-cli", "-datadir=/var/lib/bitstar"]
POOL_STATS_FILE = os.getenv("BITSTAR_POOL_STATS_FILE", "/var/lib/bitstar/pool-stats.json")
POOL_ENDPOINT = os.getenv("BITSTAR_POOL_ENDPOINT", "stratum+tcp://pool.bitstarcoin.org:3333")
POOL_MODE = os.getenv("BITSTAR_POOL_MODE", "solo_public_test_pool")
GENESIS_HASH = "00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49"
SEED_NODES = [
    {"name": "seed1.bitstarcoin.org", "host": "seed1.bitstarcoin.org", "port": 21333},
    {"name": "seed2.bitstarcoin.org", "host": "seed2.bitstarcoin.org", "port": 21333},
]


def run_cli(*args):
    process = subprocess.run(
        CLI + [str(arg) for arg in args],
        capture_output=True,
        text=True,
        timeout=8,
    )
    if process.returncode != 0:
        message = (process.stderr or process.stdout).strip()
        raise RuntimeError(message or "bitstar-cli command failed")

    output = process.stdout.strip()
    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return output


def block_summary(height):
    block_hash = run_cli("getblockhash", height)
    block = run_cli("getblock", block_hash, 1)
    return {
        "height": block.get("height", height),
        "hash": block.get("hash", block_hash),
        "time": block.get("time"),
        "tx_count": len(block.get("tx", [])),
        "size": block.get("size"),
        "weight": block.get("weight"),
        "confirmations": block.get("confirmations"),
    }


def latest_blocks(height, limit=10):
    blocks = []
    for current_height in range(height, max(-1, height - limit), -1):
        blocks.append(block_summary(current_height))
    return blocks


def public_peer(peer):
    return {
        "addr": peer.get("addr"),
        "network": peer.get("network"),
        "inbound": peer.get("inbound"),
        "subver": peer.get("subver"),
        "synced_headers": peer.get("synced_headers"),
        "synced_blocks": peer.get("synced_blocks"),
        "connection_type": peer.get("connection_type"),
    }


def int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def float_value(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def public_worker_name(name):
    text = str(name or "unknown")
    if len(text) <= 24:
        return text
    return f"{text[:12]}...{text[-8:]}"


def public_workers(workers):
    if not isinstance(workers, dict):
        return []

    rows = []
    for name, worker in workers.items():
        if not isinstance(worker, dict):
            continue
        rows.append(
            {
                "worker": public_worker_name(name),
                "active_connections": int_value(worker.get("active_connections")),
                "accepted_shares": int_value(worker.get("accepted_shares")),
                "submitted_shares": int_value(worker.get("submitted_shares")),
                "candidate_blocks": int_value(worker.get("candidate_blocks")),
                "submitblock_success": int_value(worker.get("submitblock_success")),
                "last_seen_at": int_value(worker.get("last_seen_at")),
                "last_accepted_share_at": int_value(worker.get("last_accepted_share_at")),
            }
        )

    rows.sort(
        key=lambda row: (
            row["active_connections"],
            row["accepted_shares"],
            row["submitted_shares"],
            row["last_seen_at"],
        ),
        reverse=True,
    )
    return rows[:10]


def public_accounting(accounting):
    if not isinstance(accounting, dict):
        accounting = {}

    return {
        "mode": accounting.get("mode", "solo_direct_coinbase"),
        "auto_payouts_enabled": bool(accounting.get("auto_payouts_enabled")),
        "custody_enabled": bool(accounting.get("custody_enabled")),
        "coinbase_maturity_confirmations": int_value(accounting.get("coinbase_maturity_confirmations"), 100),
        "history_snapshots_enabled": bool(accounting.get("history_snapshots_enabled")),
        "history_interval_seconds": int_value(accounting.get("history_interval_seconds")),
    }


def empty_pool_summary(message):
    return {
        "available": False,
        "pool": "BitStar Stratum solo test pool",
        "mode": POOL_MODE,
        "endpoint": POOL_ENDPOINT,
        "accounting": public_accounting({}),
        "message": message,
        "generated_at": int(time.time()),
    }


def pool_summary():
    stats_path = Path(POOL_STATS_FILE)
    try:
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return empty_pool_summary("pool stats are not published on this node yet")
    except json.JSONDecodeError:
        return empty_pool_summary("pool stats file is not valid JSON")

    listen = stats.get("listen", {}) if isinstance(stats.get("listen"), dict) else {}
    counters = stats.get("counters", {}) if isinstance(stats.get("counters"), dict) else {}
    connections = stats.get("connections", {}) if isinstance(stats.get("connections"), dict) else {}
    workers = public_workers(stats.get("workers", {}))
    accounting = public_accounting(stats.get("accounting", {}))

    return {
        "available": True,
        "pool": stats.get("pool", "BitStar Stratum solo test pool"),
        "mode": POOL_MODE,
        "endpoint": POOL_ENDPOINT,
        "started_at": int_value(stats.get("started_at")),
        "updated_at": int_value(stats.get("updated_at")),
        "uptime_seconds": int_value(stats.get("uptime_seconds")),
        "share_difficulty": float_value(listen.get("share_difficulty")),
        "refresh_seconds": int_value(listen.get("refresh_seconds")),
        "active_connections": int_value(connections.get("active")),
        "authorized_connections": int_value(connections.get("authorized")),
        "known_workers": len(stats.get("workers", {})) if isinstance(stats.get("workers"), dict) else 0,
        "total_connections": int_value(counters.get("total_connections")),
        "active_connections_peak": int_value(counters.get("active_connections_peak")),
        "authorization_rejected": int_value(counters.get("authorization_rejected")),
        "jobs_sent": int_value(counters.get("jobs_sent")),
        "clean_jobs_sent": int_value(counters.get("clean_jobs_sent")),
        "submitted_shares": int_value(counters.get("submitted_shares")),
        "accepted_shares": int_value(counters.get("accepted_shares")),
        "rejected_low_difficulty": int_value(counters.get("rejected_low_difficulty")),
        "stale_shares": int_value(counters.get("stale_shares")),
        "invalid_shares": int_value(counters.get("invalid_shares")),
        "candidate_blocks": int_value(counters.get("candidate_blocks")),
        "submitblock_success": int_value(counters.get("submitblock_success")),
        "submitblock_rejected": int_value(counters.get("submitblock_rejected")),
        "submitblock_failed": int_value(counters.get("submitblock_failed")),
        "accounting": accounting,
        "workers": workers,
        "generated_at": int(time.time()),
    }


def explorer_summary():
    chain = run_cli("getblockchaininfo")
    network = run_cli("getnetworkinfo")
    peers = run_cli("getpeerinfo")
    height = int(chain.get("blocks", 0))

    return {
        "name": "BitStar",
        "ticker": "BST",
        "chain": chain.get("chain"),
        "height": height,
        "headers": chain.get("headers"),
        "bestblockhash": chain.get("bestblockhash"),
        "genesis_hash": GENESIS_HASH,
        "difficulty": chain.get("difficulty"),
        "mediantime": chain.get("mediantime"),
        "verificationprogress": chain.get("verificationprogress"),
        "initialblockdownload": chain.get("initialblockdownload"),
        "size_on_disk": chain.get("size_on_disk"),
        "pruned": chain.get("pruned"),
        "warnings": chain.get("warnings", []),
        "version": network.get("subversion"),
        "protocolversion": network.get("protocolversion"),
        "connections": network.get("connections"),
        "peers": [public_peer(peer) for peer in peers],
        "seeds": SEED_NODES,
        "latest_blocks": latest_blocks(height),
        "generated_at": int(time.time()),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "BitStarExplorer/0.1"

    def add_common_headers(self, content_type):
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")

    def write_json(self, status, payload):
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.add_common_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_text(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.add_common_headers("text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.add_common_headers("text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        try:
            if path == "/":
                self.write_json(
                    200,
                    {
                        "service": "BitStar Explorer API",
                        "endpoints": [
                            "/healthz",
                            "/api/summary",
                            "/api/block/<height-or-hash>",
                            "/api/pool",
                        ],
                    },
                )
                return

            if path == "/healthz":
                self.write_text(200, "ok\n")
                return

            if path == "/api/summary":
                self.write_json(200, explorer_summary())
                return

            if path == "/api/pool":
                self.write_json(200, pool_summary())
                return

            if path.startswith("/api/block/"):
                ident = urllib.parse.unquote(path.removeprefix("/api/block/")).strip()
                if ident.isdecimal():
                    block_hash = run_cli("getblockhash", int(ident))
                else:
                    block_hash = ident
                self.write_json(200, run_cli("getblock", block_hash, 2))
                return

            self.write_json(404, {"error": "not_found"})
        except Exception as exc:
            self.write_json(502, {"error": "explorer_backend_error", "message": str(exc)})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"BitStar Explorer API listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
