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
import itertools
import json
import logging
import os
from pathlib import Path
import secrets
import sqlite3
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
DRY_RUN_LEDGER_SCHEMA_VERSION = 1
DRY_RUN_LEDGER_STORAGE_MEMORY = "memory"
DRY_RUN_LEDGER_STORAGE_JSON = "local_json"
DRY_RUN_LEDGER_STORAGE_SQLITE = "sqlite"
DRY_RUN_LEDGER_COUNTER_KEYS = (
    "submitted_shares",
    "accepted_shares",
    "candidate_blocks",
    "accepted_blocks",
    "rejected_blocks",
    "failed_blocks",
)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_timestamp(value: Any) -> float | None:
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return timestamp


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


def push_script_int(value: int) -> bytes:
    if value == -1:
        return b"\x4f"
    if value == 0:
        return b"\x00"
    if 1 <= value <= 16:
        return bytes([0x50 + value])
    return push_data(script_num(value))


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


def swab32(data: bytes) -> bytes:
    if len(data) % 4:
        return data
    return b"".join(data[index : index + 4][::-1] for index in range(0, len(data), 4))


def unique_byte_options(options: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    seen: set[bytes] = set()
    result: list[tuple[str, bytes]] = []
    for label, value in options:
        if value in seen:
            continue
        seen.add(value)
        result.append((label, value))
    return result


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

    @property
    def previous_hash_stratum(self) -> str:
        # Bitcoin Stratum miners byte-swap header words internally, so prevhash
        # is sent with 4-byte words swapped from the consensus header order.
        return swab32(bytes.fromhex(self.previous_hash_le)).hex()

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

    def block_header_candidates(self, coinbase_hash: bytes, ntime: str, nonce: str) -> list[tuple[str, bytes]]:
        version_wire = bytes.fromhex(self.version_hex)
        previous_display = bytes.fromhex(self.previous_hash)
        previous_wire = bytes.fromhex(self.previous_hash_stratum)
        bits_wire = bytes.fromhex(self.bits)
        ntime_wire = bytes.fromhex(ntime)
        nonce_wire = bytes.fromhex(nonce)

        if len(version_wire) != 4 or len(bits_wire) != 4 or len(ntime_wire) != 4 or len(nonce_wire) != 4:
            raise ValueError("invalid header field length")

        version_options = unique_byte_options(
            [
                ("version-consensus", ser_uint32(self.version)),
                ("version-wire", version_wire),
            ]
        )
        previous_options = unique_byte_options(
            [
                ("prev-consensus", previous_display[::-1]),
                ("prev-display", previous_display),
                ("prev-wire-swab32", swab32(previous_wire)),
                ("prev-display-swab32", swab32(previous_display)),
            ]
        )
        merkle_options = unique_byte_options(
            [
                ("merkle-consensus", coinbase_hash),
                ("merkle-display", coinbase_hash[::-1]),
                ("merkle-swab32", swab32(coinbase_hash)),
            ]
        )
        time_options = unique_byte_options(
            [
                ("ntime-consensus", ser_uint32(int(ntime, 16))),
                ("ntime-wire", ntime_wire),
            ]
        )
        bits_options = unique_byte_options(
            [
                ("bits-consensus", bits_wire[::-1]),
                ("bits-wire", bits_wire),
            ]
        )
        nonce_options = unique_byte_options(
            [
                ("nonce-consensus", nonce_wire[::-1]),
                ("nonce-wire", nonce_wire),
            ]
        )

        candidates: list[tuple[str, bytes]] = []
        for parts in itertools.product(
            version_options,
            previous_options,
            merkle_options,
            time_options,
            bits_options,
            nonce_options,
        ):
            label = ",".join(part[0] for part in parts)
            header = b"".join(part[1] for part in parts)
            candidates.append((label, header))
        return candidates

    def block_hex(self, extranonce2: str, ntime: str, nonce: str) -> str:
        coinbase = self.coinbase(extranonce2)
        coinbase_hash = sha256d(coinbase)
        header = self.block_header(coinbase_hash, ntime, nonce)
        return (header + ser_varint(1) + coinbase).hex()

    def block_hex_from_header(self, header: bytes, extranonce2: str) -> str:
        coinbase = self.coinbase(extranonce2)
        return (header + ser_varint(1) + coinbase).hex()

    def notify_params(self, clean_jobs: bool) -> list[Any]:
        return [
            self.job_id,
            self.previous_hash_stratum,
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
        self.server.note_job_sent(self.worker_name, job.height, clean_jobs)
        if clean_jobs:
            logging.info(
                "sent clean job=%s height=%s worker=%s peer=%s",
                job.job_id,
                job.height,
                self.worker_name,
                self.peer,
            )
        else:
            logging.debug(
                "sent job=%s height=%s worker=%s peer=%s",
                job.job_id,
                job.height,
                self.worker_name,
                self.peer,
            )

    async def handle(self) -> None:
        self.server.note_client_connected()
        logging.info("client connected peer=%s extranonce1=%s", self.peer, self.extranonce1)
        try:
            while line := await self.reader.readline():
                try:
                    request = json.loads(line.decode())
                except json.JSONDecodeError:
                    logging.warning("bad json from peer=%s", self.peer)
                    continue

                await self.dispatch(request)
        except ConnectionResetError:
            logging.info("client reset connection peer=%s", self.peer)
        finally:
            self.server.clients.discard(self)
            self.server.note_client_disconnected()
            if self.authorized:
                self.server.note_worker_disconnected(self.worker_name)
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
            self.server.note_authorization_rejected(worker_name)
            await self.result(request_id, False)
            return

        self.authorized = True
        self.worker_name = worker_name
        self.payout_address = payout_address
        self.server.note_worker_authorized(worker_name)
        await self.result(request_id, True)
        await self.send_job(clean_jobs=True)
        logging.info("authorized worker=%s payout=%s peer=%s", worker_name, payout_address, self.peer)

    async def submit(self, request_id: Any, params: list[Any]) -> None:
        worker_name = str(params[0]) if params else self.worker_name
        self.server.note_share_submitted(worker_name)
        if len(params) < 5:
            self.server.note_invalid_share(worker_name, "missing submit parameters")
            await self.error(request_id, 20, "mining.submit requires worker, job, extranonce2, ntime, nonce")
            return

        worker_name, job_id, extranonce2, ntime, nonce = [str(item) for item in params[:5]]
        job = self.jobs.get(job_id)
        if job is None:
            self.server.note_stale_share(worker_name)
            await self.error(request_id, 21, "stale job")
            return

        try:
            coinbase = job.coinbase(extranonce2)
            coinbase_hash = sha256d(coinbase)
            candidates = []
            for label, header in job.block_header_candidates(coinbase_hash, ntime, nonce):
                header_hash = sha256d(header)
                header_hash_int = int.from_bytes(header_hash, "little")
                candidates.append((header_hash_int, header_hash, header, label))
        except Exception as exc:
            self.server.note_invalid_share(worker_name, str(exc))
            await self.error(request_id, 20, f"invalid share: {exc}")
            return

        candidates.sort(key=lambda item: item[0])
        header_hash_int, header_hash, header, header_variant = candidates[0]
        display_hash = header_hash[::-1].hex()

        if header_hash_int > job.share_target:
            share_difficulty = Decimal(DIFF1_TARGET) / Decimal(max(header_hash_int, 1))
            self.server.note_low_difficulty_share(worker_name, share_difficulty, display_hash)
            logging.debug(
                "rejected low-difficulty share worker=%s job=%s diff=%s required=%s best_variant=%s hash=%s peer=%s",
                worker_name,
                job_id,
                share_difficulty,
                self.server.share_difficulty,
                header_variant,
                display_hash,
                self.peer,
            )
            await self.error(request_id, 23, "low difficulty share")
            return

        self.server.note_accepted_share(worker_name, display_hash)
        logging.debug(
            "accepted share worker=%s job=%s hash=%s variant=%s peer=%s",
            worker_name,
            job_id,
            display_hash,
            header_variant,
            self.peer,
        )

        block_accepted = False
        if header_hash_int <= job.target:
            self.server.note_candidate_block(worker_name, job.height, display_hash)
            block_hex = job.block_hex_from_header(header, extranonce2)
            try:
                submit_result = self.server.rpc.submitblock(block_hex)
                self.server.note_submitblock_result(worker_name, submit_result)
                block_accepted = submit_result in (None, "")
                log = logging.warning if block_accepted else logging.info
                log(
                    "submitted candidate block hash=%s height=%s result=%s variant=%s accepted=%s",
                    display_hash,
                    job.height,
                    submit_result,
                    header_variant,
                    block_accepted,
                )
            except Exception as exc:
                self.server.note_submitblock_exception(worker_name, str(exc))
                logging.exception("submitblock failed hash=%s height=%s error=%s", display_hash, job.height, exc)
                await self.error(request_id, 22, f"submitblock failed: {exc}")
                return

        await self.result(request_id, True)
        if block_accepted:
            await self.server.broadcast_jobs(clean_jobs=True)


class StratumServer:
    def __init__(
        self,
        rpc: BitStarCli,
        host: str,
        port: int,
        share_difficulty: Decimal,
        extranonce2_size: int,
        refresh_seconds: int,
        stats_file: str,
        stats_history_file: str,
        stats_history_seconds: int,
        dry_run_ledger_file: str,
        dry_run_ledger_db: str,
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
        self.started_at = time.time()
        self.stats_file = stats_file
        self.stats_history_file = stats_history_file
        self.stats_history_seconds = stats_history_seconds
        self.dry_run_ledger_file = dry_run_ledger_file
        self.dry_run_ledger_db = dry_run_ledger_db
        self._stats_dirty = True
        self._last_stats_write = 0.0
        self._last_stats_history_write = 0.0
        self.counters: dict[str, int] = {
            "total_connections": 0,
            "active_connections_peak": 0,
            "authorization_rejected": 0,
            "jobs_sent": 0,
            "clean_jobs_sent": 0,
            "submitted_shares": 0,
            "accepted_shares": 0,
            "rejected_low_difficulty": 0,
            "stale_shares": 0,
            "invalid_shares": 0,
            "candidate_blocks": 0,
            "submitblock_success": 0,
            "submitblock_rejected": 0,
            "submitblock_failed": 0,
        }
        self.workers: dict[str, dict[str, Any]] = {}
        self.dry_run_ledger_started_at = self.started_at
        self.dry_run_totals: dict[str, int] = {key: 0 for key in DRY_RUN_LEDGER_COUNTER_KEYS}
        self.dry_run_workers: dict[str, dict[str, Any]] = {}
        self.load_dry_run_ledger()

    def dry_run_ledger_persistent(self) -> bool:
        return bool(self.dry_run_ledger_db or self.dry_run_ledger_file)

    def dry_run_ledger_storage(self) -> str:
        if self.dry_run_ledger_db:
            return DRY_RUN_LEDGER_STORAGE_SQLITE
        if self.dry_run_ledger_file:
            return DRY_RUN_LEDGER_STORAGE_JSON
        return DRY_RUN_LEDGER_STORAGE_MEMORY

    def _worker(self, worker_name: str) -> dict[str, Any]:
        name = worker_name or "unknown"
        return self.workers.setdefault(
            name,
            {
                "active_connections": 0,
                "authorizations": 0,
                "jobs_sent": 0,
                "submitted_shares": 0,
                "accepted_shares": 0,
                "rejected_low_difficulty": 0,
                "stale_shares": 0,
                "invalid_shares": 0,
                "candidate_blocks": 0,
                "submitblock_success": 0,
                "submitblock_rejected": 0,
                "submitblock_failed": 0,
                "last_seen_at": None,
                "last_share_at": None,
                "last_accepted_share_at": None,
                "last_share_difficulty": None,
                "last_share_hash": None,
                "last_candidate_block": None,
                "last_error": None,
            },
        )

    def _dry_run_worker(self, worker_name: str) -> dict[str, Any]:
        name = worker_name or "unknown"
        return self.dry_run_workers.setdefault(
            name,
            {
                "submitted_shares": 0,
                "accepted_shares": 0,
                "candidate_blocks": 0,
                "accepted_blocks": 0,
                "rejected_blocks": 0,
                "failed_blocks": 0,
                "last_share_at": None,
                "last_accepted_share_at": None,
            },
        )

    def init_dry_run_sqlite(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dry_run_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dry_run_totals (
                counter TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dry_run_workers (
                worker TEXT PRIMARY KEY,
                submitted_shares INTEGER NOT NULL DEFAULT 0,
                accepted_shares INTEGER NOT NULL DEFAULT 0,
                candidate_blocks INTEGER NOT NULL DEFAULT 0,
                accepted_blocks INTEGER NOT NULL DEFAULT 0,
                rejected_blocks INTEGER NOT NULL DEFAULT 0,
                failed_blocks INTEGER NOT NULL DEFAULT 0,
                last_share_at REAL,
                last_accepted_share_at REAL,
                updated_at REAL NOT NULL
            )
            """
        )

    def connect_dry_run_sqlite(self) -> sqlite3.Connection:
        path = Path(self.dry_run_ledger_db)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        self.init_dry_run_sqlite(conn)
        return conn

    def load_dry_run_sqlite_ledger(self) -> bool:
        if not self.dry_run_ledger_db:
            return False

        path = Path(self.dry_run_ledger_db)
        existed = path.exists()
        try:
            with contextlib.closing(self.connect_dry_run_sqlite()) as conn:
                with conn:
                    if not existed:
                        return False

                    meta = {
                        row["key"]: row["value"]
                        for row in conn.execute("SELECT key, value FROM dry_run_meta")
                    }
                    total_rows = list(conn.execute("SELECT counter, value FROM dry_run_totals"))
                    worker_rows = list(
                        conn.execute(
                            """
                            SELECT worker, submitted_shares, accepted_shares,
                                   candidate_blocks, accepted_blocks, rejected_blocks,
                                   failed_blocks, last_share_at, last_accepted_share_at
                            FROM dry_run_workers
                            """
                        )
                    )
        except Exception:
            logging.exception("failed to read dry-run SQLite ledger %s", path)
            return False

        if not meta and not total_rows and not worker_rows:
            return False

        for row in total_rows:
            key = str(row["counter"])
            if key in self.dry_run_totals:
                self.dry_run_totals[key] = safe_int(row["value"])

        for row in worker_rows:
            worker_name = str(row["worker"] or "unknown")
            worker = self._dry_run_worker(worker_name)
            for key in DRY_RUN_LEDGER_COUNTER_KEYS:
                worker[key] = safe_int(row[key])
            worker["last_share_at"] = safe_timestamp(row["last_share_at"])
            worker["last_accepted_share_at"] = safe_timestamp(row["last_accepted_share_at"])

        loaded_start = safe_timestamp(meta.get("window_started_at"))
        if loaded_start is not None:
            self.dry_run_ledger_started_at = loaded_start
        logging.info("loaded dry-run SQLite ledger %s workers=%d", path, len(self.dry_run_workers))
        return True

    def load_dry_run_json_ledger(self) -> bool:
        if not self.dry_run_ledger_file:
            return False

        path = Path(self.dry_run_ledger_file)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return False
        except json.JSONDecodeError:
            logging.warning("dry-run ledger file is not valid JSON: %s", path)
            return False
        except Exception:
            logging.exception("failed to read dry-run ledger file %s", path)
            return False

        totals = data.get("totals", {}) if isinstance(data, dict) else {}
        if isinstance(totals, dict):
            for key in DRY_RUN_LEDGER_COUNTER_KEYS:
                self.dry_run_totals[key] = safe_int(totals.get(key))

        rows = data.get("workers", []) if isinstance(data, dict) else []
        if isinstance(rows, dict):
            iterable_rows = [dict(value, worker=name) for name, value in rows.items() if isinstance(value, dict)]
        elif isinstance(rows, list):
            iterable_rows = [row for row in rows if isinstance(row, dict)]
        else:
            iterable_rows = []

        for row in iterable_rows:
            worker_name = str(row.get("worker") or "unknown")
            worker = self._dry_run_worker(worker_name)
            for key in DRY_RUN_LEDGER_COUNTER_KEYS:
                if key in worker:
                    worker[key] = safe_int(row.get(key))
            worker["last_share_at"] = safe_timestamp(row.get("last_share_at"))
            worker["last_accepted_share_at"] = safe_timestamp(row.get("last_accepted_share_at"))

        loaded_start = safe_timestamp(data.get("window_started_at")) if isinstance(data, dict) else None
        if loaded_start is not None:
            self.dry_run_ledger_started_at = loaded_start
        logging.info("loaded dry-run ledger file %s workers=%d", path, len(self.dry_run_workers))
        return True

    def load_dry_run_ledger(self) -> None:
        loaded = False
        if self.dry_run_ledger_db:
            loaded = self.load_dry_run_sqlite_ledger()
        if not loaded and self.dry_run_ledger_file:
            self.load_dry_run_json_ledger()

    def mark_stats_dirty(self) -> None:
        self._stats_dirty = True

    def note_client_connected(self) -> None:
        self.counters["total_connections"] += 1
        active = len(self.clients)
        if active > self.counters["active_connections_peak"]:
            self.counters["active_connections_peak"] = active
        self.mark_stats_dirty()

    def note_client_disconnected(self) -> None:
        self.mark_stats_dirty()

    def note_authorization_rejected(self, worker_name: str) -> None:
        self.counters["authorization_rejected"] += 1
        worker = self._worker(worker_name)
        worker["last_seen_at"] = time.time()
        worker["last_error"] = "authorization rejected"
        self.mark_stats_dirty()

    def note_worker_authorized(self, worker_name: str) -> None:
        worker = self._worker(worker_name)
        worker["active_connections"] += 1
        worker["authorizations"] += 1
        worker["last_seen_at"] = time.time()
        self.mark_stats_dirty()

    def note_worker_disconnected(self, worker_name: str) -> None:
        worker = self._worker(worker_name)
        worker["active_connections"] = max(0, int(worker["active_connections"]) - 1)
        worker["last_seen_at"] = time.time()
        self.mark_stats_dirty()

    def note_job_sent(self, worker_name: str, height: int, clean_jobs: bool) -> None:
        self.counters["jobs_sent"] += 1
        if clean_jobs:
            self.counters["clean_jobs_sent"] += 1
        worker = self._worker(worker_name)
        worker["jobs_sent"] += 1
        worker["last_job_height"] = height
        worker["last_seen_at"] = time.time()
        self.mark_stats_dirty()

    def note_share_submitted(self, worker_name: str) -> None:
        self.counters["submitted_shares"] += 1
        worker = self._worker(worker_name)
        worker["submitted_shares"] += 1
        worker["last_share_at"] = time.time()
        worker["last_seen_at"] = worker["last_share_at"]
        dry_worker = self._dry_run_worker(worker_name)
        dry_worker["submitted_shares"] += 1
        dry_worker["last_share_at"] = worker["last_share_at"]
        self.dry_run_totals["submitted_shares"] += 1
        self.mark_stats_dirty()

    def note_low_difficulty_share(self, worker_name: str, difficulty: Decimal, share_hash: str) -> None:
        self.counters["rejected_low_difficulty"] += 1
        worker = self._worker(worker_name)
        worker["rejected_low_difficulty"] += 1
        worker["last_share_difficulty"] = str(difficulty)
        worker["last_share_hash"] = share_hash
        worker["last_error"] = "low difficulty share"
        self.mark_stats_dirty()

    def note_stale_share(self, worker_name: str) -> None:
        self.counters["stale_shares"] += 1
        worker = self._worker(worker_name)
        worker["stale_shares"] += 1
        worker["last_error"] = "stale job"
        self.mark_stats_dirty()

    def note_invalid_share(self, worker_name: str, error: str) -> None:
        self.counters["invalid_shares"] += 1
        worker = self._worker(worker_name)
        worker["invalid_shares"] += 1
        worker["last_error"] = error
        self.mark_stats_dirty()

    def note_accepted_share(self, worker_name: str, share_hash: str) -> None:
        self.counters["accepted_shares"] += 1
        worker = self._worker(worker_name)
        worker["accepted_shares"] += 1
        worker["last_accepted_share_at"] = time.time()
        worker["last_share_hash"] = share_hash
        worker["last_error"] = None
        dry_worker = self._dry_run_worker(worker_name)
        dry_worker["accepted_shares"] += 1
        dry_worker["last_accepted_share_at"] = worker["last_accepted_share_at"]
        self.dry_run_totals["accepted_shares"] += 1
        self.mark_stats_dirty()

    def note_candidate_block(self, worker_name: str, height: int, block_hash: str) -> None:
        self.counters["candidate_blocks"] += 1
        worker = self._worker(worker_name)
        worker["candidate_blocks"] += 1
        worker["last_candidate_block"] = {"height": height, "hash": block_hash, "time": time.time()}
        dry_worker = self._dry_run_worker(worker_name)
        dry_worker["candidate_blocks"] += 1
        self.dry_run_totals["candidate_blocks"] += 1
        self.mark_stats_dirty()

    def note_submitblock_result(self, worker_name: str, result: Any) -> None:
        if result in (None, ""):
            counter = "submitblock_success"
            dry_counter = "accepted_blocks"
            error = None
        else:
            counter = "submitblock_rejected"
            dry_counter = "rejected_blocks"
            error = str(result)
        self.counters[counter] += 1
        worker = self._worker(worker_name)
        worker[counter] += 1
        worker["last_error"] = error
        dry_worker = self._dry_run_worker(worker_name)
        dry_worker[dry_counter] += 1
        self.dry_run_totals[dry_counter] += 1
        self.mark_stats_dirty()

    def note_submitblock_exception(self, worker_name: str, error: str) -> None:
        self.counters["submitblock_failed"] += 1
        worker = self._worker(worker_name)
        worker["submitblock_failed"] += 1
        worker["last_error"] = error
        dry_worker = self._dry_run_worker(worker_name)
        dry_worker["failed_blocks"] += 1
        self.dry_run_totals["failed_blocks"] += 1
        self.mark_stats_dirty()

    def dry_run_ledger_snapshot(self, now: float) -> dict[str, Any]:
        total_accepted = int(self.dry_run_totals["accepted_shares"])
        rows = []
        for worker_name, worker in self.dry_run_workers.items():
            accepted_shares = int(worker.get("accepted_shares", 0))
            share_weight_ppm = 0
            if total_accepted > 0:
                share_weight_ppm = (accepted_shares * 1_000_000) // total_accepted

            rows.append(
                {
                    "worker": worker_name,
                    "accepted_shares": accepted_shares,
                    "submitted_shares": int(worker.get("submitted_shares", 0)),
                    "share_weight_ppm": share_weight_ppm,
                    "candidate_blocks": int(worker.get("candidate_blocks", 0)),
                    "accepted_blocks": int(worker.get("accepted_blocks", 0)),
                    "rejected_blocks": int(worker.get("rejected_blocks", 0)),
                    "failed_blocks": int(worker.get("failed_blocks", 0)),
                    "last_share_at": worker.get("last_share_at"),
                    "last_accepted_share_at": worker.get("last_accepted_share_at"),
                }
            )

        rows.sort(
            key=lambda row: (
                row["share_weight_ppm"],
                row["accepted_shares"],
                row["candidate_blocks"],
            ),
            reverse=True,
        )

        return {
            "schema_version": DRY_RUN_LEDGER_SCHEMA_VERSION,
            "mode": "dry_run_only",
            "reward_method": "proportional_share_report_only",
            "payouts_broadcast": False,
            "persistent": self.dry_run_ledger_persistent(),
            "storage": self.dry_run_ledger_storage(),
            "database_backed": bool(self.dry_run_ledger_db),
            "json_mirror": bool(self.dry_run_ledger_file),
            "backup_required": bool(self.dry_run_ledger_db),
            "window_started_at": self.dry_run_ledger_started_at,
            "window_updated_at": now,
            "totals": dict(self.dry_run_totals),
            "workers": rows,
        }

    def stats_snapshot(self) -> dict[str, Any]:
        now = time.time()
        return {
            "pool": "BitStar Stratum solo test pool",
            "started_at": self.started_at,
            "updated_at": now,
            "uptime_seconds": int(now - self.started_at),
            "listen": {
                "host": self.host,
                "port": self.port,
                "share_difficulty": str(self.share_difficulty),
                "refresh_seconds": self.refresh_seconds,
            },
            "connections": {
                "active": len(self.clients),
                "authorized": sum(1 for client in self.clients if client.authorized),
            },
            "accounting": {
                "mode": "solo_direct_coinbase",
                "auto_payouts_enabled": False,
                "custody_enabled": False,
                "dry_run_ledger_enabled": True,
                "dry_run_payouts_broadcast": False,
                "dry_run_reward_method": "proportional_share_report_only",
                "dry_run_ledger_persistent": self.dry_run_ledger_persistent(),
                "dry_run_ledger_storage": self.dry_run_ledger_storage(),
                "dry_run_ledger_database": bool(self.dry_run_ledger_db),
                "dry_run_ledger_json_mirror": bool(self.dry_run_ledger_file),
                "dry_run_ledger_backup_required": bool(self.dry_run_ledger_db),
                "coinbase_maturity_confirmations": 100,
                "history_snapshots_enabled": bool(self.stats_history_file),
                "history_interval_seconds": self.stats_history_seconds if self.stats_history_file else 0,
            },
            "dry_run_ledger": self.dry_run_ledger_snapshot(now),
            "counters": dict(self.counters),
            "workers": self.workers,
        }

    def write_stats_history(self, snapshot: dict[str, Any], now: float) -> None:
        if not self.stats_history_file or self.stats_history_seconds <= 0:
            return
        if now - self._last_stats_history_write < self.stats_history_seconds:
            return

        path = Path(self.stats_history_file)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(snapshot, separators=(",", ":"), sort_keys=True))
                handle.write("\n")
            self._last_stats_history_write = now
        except Exception:
            logging.exception("failed to append stats history file %s", path)

    def write_dry_run_sqlite_ledger(self, ledger: dict[str, Any]) -> bool:
        if not self.dry_run_ledger_db:
            return True

        try:
            with contextlib.closing(self.connect_dry_run_sqlite()) as conn:
                with conn:
                    meta_values = {
                        "schema_version": str(safe_int(ledger.get("schema_version"), DRY_RUN_LEDGER_SCHEMA_VERSION)),
                        "mode": str(ledger.get("mode", "dry_run_only")),
                        "reward_method": str(ledger.get("reward_method", "proportional_share_report_only")),
                        "payouts_broadcast": "false",
                        "window_started_at": str(float(ledger.get("window_started_at") or self.dry_run_ledger_started_at)),
                        "window_updated_at": str(float(ledger.get("window_updated_at") or time.time())),
                        "storage": DRY_RUN_LEDGER_STORAGE_SQLITE,
                    }
                    for key, value in meta_values.items():
                        conn.execute(
                            """
                            INSERT INTO dry_run_meta(key, value)
                            VALUES (?, ?)
                            ON CONFLICT(key) DO UPDATE SET value = excluded.value
                            """,
                            (key, value),
                        )

                    totals = ledger.get("totals", {}) if isinstance(ledger.get("totals"), dict) else {}
                    for key in DRY_RUN_LEDGER_COUNTER_KEYS:
                        conn.execute(
                            """
                            INSERT INTO dry_run_totals(counter, value)
                            VALUES (?, ?)
                            ON CONFLICT(counter) DO UPDATE SET value = excluded.value
                            """,
                            (key, safe_int(totals.get(key))),
                        )

                    updated_at = safe_timestamp(ledger.get("window_updated_at")) or time.time()
                    workers = ledger.get("workers", []) if isinstance(ledger.get("workers"), list) else []
                    for row in workers:
                        if not isinstance(row, dict):
                            continue
                        worker_name = str(row.get("worker") or "unknown")
                        conn.execute(
                            """
                            INSERT INTO dry_run_workers(
                                worker, submitted_shares, accepted_shares,
                                candidate_blocks, accepted_blocks, rejected_blocks,
                                failed_blocks, last_share_at, last_accepted_share_at,
                                updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(worker) DO UPDATE SET
                                submitted_shares = excluded.submitted_shares,
                                accepted_shares = excluded.accepted_shares,
                                candidate_blocks = excluded.candidate_blocks,
                                accepted_blocks = excluded.accepted_blocks,
                                rejected_blocks = excluded.rejected_blocks,
                                failed_blocks = excluded.failed_blocks,
                                last_share_at = excluded.last_share_at,
                                last_accepted_share_at = excluded.last_accepted_share_at,
                                updated_at = excluded.updated_at
                            """,
                            (
                                worker_name,
                                safe_int(row.get("submitted_shares")),
                                safe_int(row.get("accepted_shares")),
                                safe_int(row.get("candidate_blocks")),
                                safe_int(row.get("accepted_blocks")),
                                safe_int(row.get("rejected_blocks")),
                                safe_int(row.get("failed_blocks")),
                                safe_timestamp(row.get("last_share_at")),
                                safe_timestamp(row.get("last_accepted_share_at")),
                                updated_at,
                            ),
                        )
            return True
        except Exception:
            logging.exception("failed to write dry-run SQLite ledger %s", self.dry_run_ledger_db)
            return False

    def write_dry_run_json_ledger(self, ledger: dict[str, Any]) -> bool:
        if not self.dry_run_ledger_file:
            return True

        path = Path(self.dry_run_ledger_file)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + ".tmp")
            tmp_path.write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")
            tmp_path.replace(path)
            return True
        except Exception:
            logging.exception("failed to write dry-run ledger file %s", path)
            return False

    def write_dry_run_ledger(self, ledger: dict[str, Any]) -> bool:
        sqlite_written = self.write_dry_run_sqlite_ledger(ledger)
        json_written = self.write_dry_run_json_ledger(ledger)
        return sqlite_written and json_written

    def write_stats(self, force: bool = False) -> None:
        if (
            not self.stats_file
            and not self.stats_history_file
            and not self.dry_run_ledger_file
            and not self.dry_run_ledger_db
        ):
            return
        now = time.time()
        if not force and (not self._stats_dirty or now - self._last_stats_write < 2):
            return

        snapshot = self.stats_snapshot()
        stats_written = True
        ledger_written = self.write_dry_run_ledger(snapshot["dry_run_ledger"])
        if self.stats_file:
            path = Path(self.stats_file)
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = path.with_suffix(path.suffix + ".tmp")
                tmp_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
                tmp_path.replace(path)
            except Exception:
                stats_written = False
                logging.exception("failed to write stats file %s", path)

        self.write_stats_history(snapshot, now)
        if stats_written and ledger_written:
            self._last_stats_write = now
            self._stats_dirty = False

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
        script_prefix = push_script_int(height) + push_data(DEFAULT_POOL_TAG)
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

    async def broadcast_jobs(self, clean_jobs: bool) -> None:
        for client in list(self.clients):
            if client.authorized:
                await client.send_job(clean_jobs=clean_jobs)

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

    async def write_stats_periodically(self) -> None:
        while True:
            await asyncio.sleep(5)
            self.write_stats(force=self._stats_dirty)

    async def serve(self) -> None:
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        sockets = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        logging.info(
            "BitStar Stratum test pool listening on %s difficulty=%s",
            sockets,
            self.share_difficulty,
        )

        self.write_stats(force=True)
        refresh_task = asyncio.create_task(self.refresh_jobs())
        stats_task = asyncio.create_task(self.write_stats_periodically())
        try:
            async with server:
                await server.serve_forever()
        finally:
            refresh_task.cancel()
            stats_task.cancel()
            self.write_stats(force=True)


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
    parser.add_argument(
        "--stats-file",
        default=os.getenv("BITSTAR_POOL_STATS_FILE", "/var/lib/bitstar/pool-stats.json"),
        help="Write a local JSON stats snapshot for operators. Use an empty value to disable.",
    )
    parser.add_argument(
        "--stats-history-file",
        default=os.getenv("BITSTAR_POOL_STATS_HISTORY_FILE", ""),
        help="Append periodic JSONL stats snapshots for operator accounting review. Empty disables history.",
    )
    parser.add_argument(
        "--stats-history-seconds",
        type=int,
        default=int(os.getenv("BITSTAR_POOL_STATS_HISTORY_SECONDS", "60")),
        help="Minimum seconds between stats history snapshots.",
    )
    parser.add_argument(
        "--dry-run-ledger-file",
        default=os.getenv("BITSTAR_POOL_DRY_RUN_LEDGER_FILE", "/var/lib/bitstar/pool-dry-run-ledger.json"),
        help="Write a JSON mirror of the dry-run share ledger. Use an empty value to disable the mirror.",
    )
    parser.add_argument(
        "--dry-run-ledger-db",
        default=os.getenv("BITSTAR_POOL_DRY_RUN_LEDGER_DB", "/var/lib/bitstar/pool-dry-run-ledger.sqlite3"),
        help="Persist the dry-run share ledger in SQLite. Use an empty value to keep it in JSON/memory only.",
    )
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
        stats_file=args.stats_file,
        stats_history_file=args.stats_history_file,
        stats_history_seconds=args.stats_history_seconds,
        dry_run_ledger_file=args.dry_run_ledger_file,
        dry_run_ledger_db=args.dry_run_ledger_db,
    )
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
