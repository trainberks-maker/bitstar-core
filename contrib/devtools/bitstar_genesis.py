#!/usr/bin/env python3
# Copyright (c) 2026 The BitStar developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

"""Generate the BitStar genesis block parameters.

This script mirrors the serialization used by CreateGenesisBlock in
src/kernel/chainparams.cpp so the genesis hash and merkle root can be
reproduced independently.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from datetime import UTC, datetime


COIN = 100_000_000
GENESIS_REWARD = 50 * COIN
GENESIS_TIME = int(datetime(2026, 8, 21, tzinfo=UTC).timestamp())
GENESIS_BITS = 0x1E0FFFF0
GENESIS_VERSION = 1
GENESIS_TIMESTAMP = b"BitStar 21/Aug/2026 fair launch - no premine - 21 million BST"
GENESIS_PUBKEY = bytes.fromhex(
    "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb"
    "649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"
)


def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def ser_compact_size(size: int) -> bytes:
    if size < 253:
        return bytes([size])
    if size <= 0xFFFF:
        return b"\xfd" + struct.pack("<H", size)
    if size <= 0xFFFF_FFFF:
        return b"\xfe" + struct.pack("<I", size)
    return b"\xff" + struct.pack("<Q", size)


def ser_script_num(value: int) -> bytes:
    if value == 0:
        return b""

    result = bytearray()
    abs_value = abs(value)
    while abs_value:
        result.append(abs_value & 0xFF)
        abs_value >>= 8

    if result[-1] & 0x80:
        result.append(0x80 if value < 0 else 0)
    elif value < 0:
        result[-1] |= 0x80

    return bytes(result)


def push_data(data: bytes) -> bytes:
    if len(data) < 76:
        return bytes([len(data)]) + data
    if len(data) <= 0xFF:
        return b"\x4c" + bytes([len(data)]) + data
    if len(data) <= 0xFFFF:
        return b"\x4d" + struct.pack("<H", len(data)) + data
    return b"\x4e" + struct.pack("<I", len(data)) + data


def genesis_coinbase() -> bytes:
    script_sig = (
        push_data(ser_script_num(486604799))
        + push_data(ser_script_num(4))
        + push_data(GENESIS_TIMESTAMP)
    )
    script_pubkey = push_data(GENESIS_PUBKEY) + b"\xac"

    tx = bytearray()
    tx += struct.pack("<i", 1)
    tx += ser_compact_size(1)
    tx += b"\x00" * 32
    tx += struct.pack("<I", 0xFFFF_FFFF)
    tx += ser_compact_size(len(script_sig))
    tx += script_sig
    tx += struct.pack("<I", 0xFFFF_FFFF)
    tx += ser_compact_size(1)
    tx += struct.pack("<q", GENESIS_REWARD)
    tx += ser_compact_size(len(script_pubkey))
    tx += script_pubkey
    tx += struct.pack("<I", 0)
    return bytes(tx)


def target_from_bits(bits: int) -> int:
    exponent = bits >> 24
    mantissa = bits & 0x00FF_FFFF
    if exponent <= 3:
        return mantissa >> (8 * (3 - exponent))
    return mantissa << (8 * (exponent - 3))


@dataclass(frozen=True)
class Genesis:
    nonce: int
    merkle_root: str
    block_hash: str
    header_hex: str
    coinbase_hex: str


def mine() -> Genesis:
    coinbase = genesis_coinbase()
    merkle_raw = sha256d(coinbase)
    target = target_from_bits(GENESIS_BITS)

    for nonce in range(0, 0xFFFF_FFFF + 1):
        header = (
            struct.pack("<i", GENESIS_VERSION)
            + b"\x00" * 32
            + merkle_raw
            + struct.pack("<III", GENESIS_TIME, GENESIS_BITS, nonce)
        )
        header_hash = sha256d(header)
        if int.from_bytes(header_hash, "little") <= target:
            return Genesis(
                nonce=nonce,
                merkle_root=merkle_raw[::-1].hex(),
                block_hash=header_hash[::-1].hex(),
                header_hex=header.hex(),
                coinbase_hex=coinbase.hex(),
            )

    raise RuntimeError("No valid nonce found")


def main() -> None:
    genesis = mine()
    print(f"timestamp: {GENESIS_TIMESTAMP.decode()}")
    print(f"time: {GENESIS_TIME}")
    print(f"bits: 0x{GENESIS_BITS:08x}")
    print(f"nonce: {genesis.nonce}")
    print(f"merkle_root: {genesis.merkle_root}")
    print(f"block_hash: {genesis.block_hash}")
    print(f"header_hex: {genesis.header_hex}")
    print(f"coinbase_hex: {genesis.coinbase_hex}")


if __name__ == "__main__":
    main()
