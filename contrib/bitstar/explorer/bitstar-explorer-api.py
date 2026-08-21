#!/usr/bin/env python3
import json
import subprocess
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "0.0.0.0"
PORT = 8090
CLI = ["/usr/local/bin/bitstar-cli", "-datadir=/var/lib/bitstar"]
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
                        "endpoints": ["/healthz", "/api/summary", "/api/block/<height-or-hash>"],
                    },
                )
                return

            if path == "/healthz":
                self.write_text(200, "ok\n")
                return

            if path == "/api/summary":
                self.write_json(200, explorer_summary())
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
