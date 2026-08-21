#!/usr/bin/env python3
"""
Minimal BitStar Stratum V1 solo test pool.

This is an early compatibility server for testing BitStar mining software. It
does not implement pooled accounting or automatic payouts. Miners authorize with
a BitStar payout address as their username; if a valid block is found, the
coinbase output pays that address directly.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import hashlib
import json
import logging
import os
import secrets
import struct
import subprocess
import time
from decimal import Decimal, getcontext
from typing import Any


getcontext().prec = 80

DIFF1_TARGET = int(
    "00000000ffff0000000000000000000000000000000000000000000000000000", 16
)
MAX_TARGET = (1 << 256) - 1
DEFAULT_POOL_TAG = b"/BitStarTestPool/"


def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def ser_uint32(value: int) -> bytes:
    return struct.pack("<I", value)


def ser_uint64(value: int) -> bytes:
    return struct.pack("<Q", value)


def ser_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative varint")
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + struct.pack("<H", value)
    if value <= 0xFFFFFFFF:
        return b"\xfe" + struct.pack("<I", value)
    return b"\xff" + struct.pack("<Q", value)


def script_num(value: int) -> bytes:
    if value == 0:
        return b""

    result = bytearray()
    negative = value < 0
    abs_value = -value if negative else value

    while abs_value:
        result.append(abs_value & 0xFF)
        abs_value >>= 8

    if result[-1] & 0x80:
        result.append(0x80 if negative else 0)
    elif negative:
        result[-1] |= 0x80

    return bytes(result)


def push_data(data: bytes) -> bytes:
    length = len(data)
    if length < 0x4C:
        return bytes([length]) + data
    if length <= 0xFF:
        return b"\x4c" + bytes([length]) + data
    if length <= 0xFFFF:
        return b"\x4d" + struct.pack("<H", length) + data
    return b"\x4e" + struct.pack("<I", length) + data


def compact_to_target(bits: str) -> int:
    raw = bytes.fromhex(bits)
    if len(raw) != 4:
        raise ValueError(f"invalid compact target: {bits}")
    exponent = raw[0]
    mantissa = int.from_bytes(raw[1:], "big")
    if exponent <= 3:
        return mantissa >> (8 * (3 - exponent))
    return mantissa << (8 * (exponent - 3))


def difficulty_to_target(difficulty: Decimal) -> int:
    if difficulty <= 0:
        raise ValueError("difficulty must be positive")
    target = int(Decimal(DIFF1_TARGET) / difficulty)
    return max(1, min(target, MAX_TARGET))


def reverse_hash_hex(hash_hex: str) -> str:
    return bytes.fromhex(hash_hex)[::-1].hex()


def extract_payout_address(worker_name: str) -> str:
    return worker_name.split(".", 1)[0].strip()


class BitStarCli:
    def __init__(self, cli: str, datadir: str, conf: str, timeout: int) -> None:
        self.cli = cli
        self.datadir = datadir
        self.conf = conf
        self.timeout = timeout
        self._address_cache: dict[str, str] = {}

    def call(self, method: str, *params: str) -> Any:
        command = [
            self.cli,
            f"-datadir={self.datadir}",
            f"-conf={self.conf}",
            method,
            *params,
        ]
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"{method} failed: {message}")

        output = result.stdout.strip()
        if not output:
            return None

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    def getmininginfo(self) -> dict[str, Any]:
        return self.call("getmininginfo")

    def getblocktemplate(self) -> dict[str, Any]:
        return self.call("getblocktemplate", '{"rules":["segwit"]}')

    def submitblock(self, block_hex: str) -> Any:
        return self.call("submitblock", block_hex)

    def script_pub_key_for_address(self, address: str) -> bytes:
        cached = self._address_cache.get(address)
        if cached:
            return bytes.fromhex(cached)

        result = self.call("validateaddress", address)
        if not isinstance(result, dict) or not result.get("isvalid"):
            raise ValueError(f"invalid BitStar address: {address}")

        script_pub_key = result.get("scriptPubKey")
        if not isinstance(script_pub_key, str):
            raise ValueError(f"address has no scriptPubKey: {address}")

        self._address_cache[address] = script_pub_key
        return bytes.fromhex(script_pub_key)


@dataclasses.dataclass
class Job:
    job_id: str
    height: int
    payout_address: str
    version: int
    previous_hash: str
    bits: str
    ntime: str
    target: int
    share_target: int
    coinb1: bytes
    coinb2: bytes
    extranonce1: str
    extranonce2_size: int
    created_at: float

    @property
    def version_hex(self) -> str:
        return f"{self.version:08x}"

    @property
    def previous_hash_le(self) -> str:
        return reverse_hash_hex(self.previous_hash)

    def coinbase(self, extranonce2: str) -> bytes:
        extranonce2_bytes = bytes.fromhex(extranonce2)
        if len(extranonce2_bytes) != self.extranonce2_size:
            raise ValueError("invalid extranonce2 size")
        return self.coinb1 + bytes.fromhex(self.extranonce1) + extranonce2_bytes + self.coinb2

    def block_header(self, coinbase_hash: bytes, ntime: str, nonce: str) -> bytes:
        return b"".join(
            [
                ser_uint32(self.version),
                bytes.fromhex(self.previous_hash)[::-1],
                coinbase_hash,
                ser_uint32(int(ntime, 16)),
                bytes.fromhex(self.bits)[::-1],
                bytes.fromhex(nonce)[::-1],
            ]
        )

    def block_hex(self, extranonce2: str, ntime: str, nonce: str) -> str:
        coinbase = self.coinbase(extranonce2)
        coinbase_hash = sha256d(coinbase)
        header = self.block_header(coinbase_hash, ntime, nonce)
        return (header + ser_varint(1) + coinbase).hex()

    def notify_params(self, clean_jobs: bool) -> list[Any]:
        return [
            self.job_id,
            self.previous_hash_le,
            self.coinb1.hex(),
            self.coinb2.hex(),
            [],
            self.version_hex,
            self.bits,
            self.ntime,
            clean_jobs,
        ]


class StratumClient:
    def __init__(
        self,
        server: "StratumServer",
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        client_id: int,
    ) -> None:
        self.server = server
        self.reader = reader
        self.writer = writer
        self.client_id = client_id
        self.peer = writer.get_extra_info("peername")
        self.extranonce1 = f"{client_id:08x}"
        self.authorized = False
        self.worker_name = ""
        self.payout_address = ""
        self.jobs: dict[str, Job] = {}

    async def send(self, payload: dict[str, Any]) -> None:
        self.writer.write(json.dumps(payload, separators=(",", ":")).encode() + b"\n")
        await self.writer.drain()

    async def result(self, request_id: Any, result: Any) -> None:
        await self.send({"id": request_id, "result": result, "error": None})

    async def error(self, request_id: Any, code: int, message: str) -> None:
        await self.send({"id": request_id, "result": None, "error": [code, message, None]})

    async def request(self, method: str, params: list[Any]) -> None:
        await self.send({"id": None, "method": method, "params": params})

    async def send_job(self, clean_jobs: bool) -> None:
        if not self.authorized:
            return

        job = await self.server.build_job(self.payout_address, self.extranonce1)
        self.jobs[job.job_id] = job
        await self.request("mining.set_difficulty", [float(self.server.share_difficulty)])
        await self.request("mining.notify", job.notify_params(clean_jobs))
        logging.info(
            "sent job=%s height=%s worker=%s peer=%s",
            job.job_id,
            job.height,
            self.worker_name,
            self.peer,
        )

    async def handle(self) -> None:
        logging.info("client connected peer=%s extranonce1=%s", self.peer, self.extranonce1)
        try:
            while line := await self.reader.readline():
                try:
                    request = json.loads(line.decode())
                except json.JSONDecodeError:
                    logging.warning("bad json from peer=%s", self.peer)
                    continue

                await self.dispatch(request)
        finally:
            self.server.clients.discard(self)
            self.writer.close()
            with contextlib.suppress(Exception):
                await self.writer.wait_closed()
            logging.info("client disconnected peer=%s", self.peer)

    async def dispatch(self, request: dict[str, Any]) -> None:
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or []

        if method == "mining.configure":
            await self.result(request_id, {})
            return

        if method == "mining.subscribe":
            subscriptions = [
                ["mining.set_difficulty", self.extranonce1],
                ["mining.notify", self.extranonce1],
            ]
            await self.result(request_id, [subscriptions, self.extranonce1, self.server.extranonce2_size])
            return

        if method == "mining.authorize":
            await self.authorize(request_id, params)
            return

        if method == "mining.submit":
            await self.submit(request_id, params)
            return

        if method in {"mining.suggest_difficulty", "mining.extranonce.subscribe"}:
            await self.result(request_id, True)
            return

        await self.error(request_id, 20, f"unsupported method: {method}")

    async def authorize(self, request_id: Any, params: list[Any]) -> None:
        if not params:
            await self.error(request_id, 24, "worker name must be a BitStar address")
            return

        worker_name = str(params[0])
        payout_address = extract_payout_address(worker_name)
        try:
            self.server.rpc.script_pub_key_for_address(payout_address)
        except Exception as exc:
            logging.warning("authorization rejected worker=%s peer=%s error=%s", worker_name, self.peer, exc)
            await self.result(request_id, False)
            return

        self.authorized = True
        self.worker_name = worker_name
        self.payout_address = payout_address
        await self.result(request_id, True)
        await self.send_job(clean_jobs=True)
        logging.info("authorized worker=%s payout=%s peer=%s", worker_name, payout_address, self.peer)

    async def submit(self, request_id: Any, params: list[Any]) -> None:
        if len(params) < 5:
            await self.error(request_id, 20, "mining.submit requires worker, job, extranonce2, ntime, nonce")
            return

        worker_name, job_id, extranonce2, ntime, nonce = [str(item) for item in params[:5]]
        job = self.jobs.get(job_id)
        if job is None:
            await self.error(request_id, 21, "stale job")
            return

        try:
            coinbase = job.coinbase(extranonce2)
            coinbase_hash = sha256d(coinbase)
            header = job.block_header(coinbase_hash, ntime, nonce)
            header_hash = sha256d(header)
            header_hash_int = int.from_bytes(header_hash, "little")
            display_hash = header_hash[::-1].hex()
        except Exception as exc:
            await self.error(request_id, 20, f"invalid share: {exc}")
            return

        if header_hash_int > job.share_target:
            await self.error(request_id, 23, "low difficulty share")
            return

        logging.info(
            "accepted share worker=%s job=%s hash=%s peer=%s",
            worker_name,
            job_id,
            display_hash,
            self.peer,
        )

        if header_hash_int <= job.target:
            block_hex = job.block_hex(extranonce2, ntime, nonce)
            try:
                submit_result = self.server.rpc.submitblock(block_hex)
                logging.warning(
                    "submitted candidate block hash=%s height=%s result=%s",
                    display_hash,
                    job.height,
                    submit_result,
                )
            except Exception as exc:
                logging.exception("submitblock failed hash=%s height=%s error=%s", display_hash, job.height, exc)
                await self.error(request_id, 22, f"submitblock failed: {exc}")
                return

        await self.result(request_id, True)


class StratumServer:
    def __init__(
        self,
        rpc: BitStarCli,
        host: str,
        port: int,
        share_difficulty: Decimal,
        extranonce2_size: int,
        refresh_seconds: int,
    ) -> None:
        self.rpc = rpc
        self.host = host
        self.port = port
        self.share_difficulty = share_difficulty
        self.share_target = difficulty_to_target(share_difficulty)
        self.extranonce2_size = extranonce2_size
        self.refresh_seconds = refresh_seconds
        self.clients: set[StratumClient] = set()
        self._client_counter = secrets.randbits(31)

    async def build_job(self, payout_address: str, extranonce1: str) -> Job:
        template = await asyncio.to_thread(self.rpc.getblocktemplate)
        script_pub_key = await asyncio.to_thread(self.rpc.script_pub_key_for_address, payout_address)

        tx_fee_total = sum(int(tx.get("fee", 0)) for tx in template.get("transactions", []))
        coinbase_value = int(template["coinbasevalue"]) - tx_fee_total
        if coinbase_value <= 0:
            raise RuntimeError("invalid coinbase value from template")

        height = int(template["height"])
        coinbase_prefix = (
            ser_uint32(2)
            + ser_varint(1)
            + (b"\x00" * 32)
            + ser_uint32(0xFFFFFFFF)
        )
        script_prefix = push_data(script_num(height)) + push_data(DEFAULT_POOL_TAG)
        script_len = len(script_prefix) + len(bytes.fromhex(extranonce1)) + self.extranonce2_size
        coinb1 = coinbase_prefix + ser_varint(script_len) + script_prefix

        outputs = [
            ser_uint64(coinbase_value) + ser_varint(len(script_pub_key)) + script_pub_key
        ]
        coinb2 = (
            ser_uint32(0xFFFFFFFF)
            + ser_varint(len(outputs))
            + b"".join(outputs)
            + ser_uint32(0)
        )

        bits = str(template["bits"])
        ntime = f"{max(int(template.get('curtime', time.time())), int(template.get('mintime', 0))):08x}"
        target = compact_to_target(bits)
        return Job(
            job_id=secrets.token_hex(4),
            height=height,
            payout_address=payout_address,
            version=int(template["version"]),
            previous_hash=str(template["previousblockhash"]),
            bits=bits,
            ntime=ntime,
            target=target,
            share_target=self.share_target,
            coinb1=coinb1,
            coinb2=coinb2,
            extranonce1=extranonce1,
            extranonce2_size=self.extranonce2_size,
            created_at=time.time(),
        )

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self._client_counter += 1
        client = StratumClient(self, reader, writer, self._client_counter)
        self.clients.add(client)
        await client.handle()

    async def refresh_jobs(self) -> None:
        last_seen_hash = ""
        while True:
            await asyncio.sleep(self.refresh_seconds)
            if not self.clients:
                continue

            try:
                template = await asyncio.to_thread(self.rpc.getblocktemplate)
                previous_hash = str(template["previousblockhash"])
                clean_jobs = previous_hash != last_seen_hash
                last_seen_hash = previous_hash
                for client in list(self.clients):
                    if client.authorized:
                        await client.send_job(clean_jobs=clean_jobs)
            except Exception:
                logging.exception("failed to refresh jobs")

    async def serve(self) -> None:
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        sockets = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        logging.info(
            "BitStar Stratum test pool listening on %s difficulty=%s",
            sockets,
            self.share_difficulty,
        )

        refresh_task = asyncio.create_task(self.refresh_jobs())
        try:
            async with server:
                await server.serve_forever()
        finally:
            refresh_task.cancel()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BitStar minimal Stratum V1 solo test pool")
    parser.add_argument("--host", default=os.getenv("BITSTAR_POOL_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("BITSTAR_POOL_PORT", "3333")))
    parser.add_argument("--cli", default=os.getenv("BITSTAR_CLI", "/usr/local/bin/bitstar-cli"))
    parser.add_argument("--datadir", default=os.getenv("BITSTAR_DATADIR", "/var/lib/bitstar"))
    parser.add_argument("--conf", default=os.getenv("BITSTAR_CONF", "/etc/bitstar/bitstar.conf"))
    parser.add_argument(
        "--share-difficulty",
        default=os.getenv("BITSTAR_POOL_SHARE_DIFFICULTY", "0.00001"),
        help="Stratum share difficulty. Low fractional values are useful for bootstrap testing.",
    )
    parser.add_argument(
        "--extranonce2-size",
        type=int,
        default=int(os.getenv("BITSTAR_POOL_EXTRANONCE2_SIZE", "4")),
    )
    parser.add_argument(
        "--refresh-seconds",
        type=int,
        default=int(os.getenv("BITSTAR_POOL_REFRESH_SECONDS", "20")),
    )
    parser.add_argument("--rpc-timeout", type=int, default=int(os.getenv("BITSTAR_RPC_TIMEOUT", "15")))
    parser.add_argument("--check", action="store_true", help="Check node RPC and exit")
    parser.add_argument("--log-level", default=os.getenv("BITSTAR_POOL_LOG_LEVEL", "INFO"))
    return parser.parse_args()


def check_rpc(rpc: BitStarCli) -> None:
    mining_info = rpc.getmininginfo()
    template = rpc.getblocktemplate()
    print(
        json.dumps(
            {
                "chain": mining_info.get("chain"),
                "blocks": mining_info.get("blocks"),
                "difficulty": mining_info.get("difficulty"),
                "template_height": template.get("height"),
                "coinbasevalue": template.get("coinbasevalue"),
                "bits": template.get("bits"),
                "previousblockhash": template.get("previousblockhash"),
            },
            indent=2,
        )
    )


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    rpc = BitStarCli(args.cli, args.datadir, args.conf, args.rpc_timeout)

    if args.check:
        check_rpc(rpc)
        return

    server = StratumServer(
        rpc=rpc,
        host=args.host,
        port=args.port,
        share_difficulty=Decimal(str(args.share_difficulty)),
        extranonce2_size=args.extranonce2_size,
        refresh_seconds=args.refresh_seconds,
    )
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
