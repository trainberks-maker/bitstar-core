#!/usr/bin/env python3
"""
Online backup and restore-drill helper for the BitStar pool dry-run ledger.

This tool intentionally does not restore over the live database. It creates
SQLite backups with the Python sqlite3 backup API, verifies them, and can copy
a backup into a temporary restore-drill database for operator validation.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any


DEFAULT_LEDGER_DB = os.getenv(
    "BITSTAR_POOL_DRY_RUN_LEDGER_DB",
    "/var/lib/bitstar/pool-dry-run-ledger.sqlite3",
)
DEFAULT_BACKUP_DIR = os.getenv(
    "BITSTAR_POOL_LEDGER_BACKUP_DIR",
    "/var/backups/bitstar/pool",
)
DEFAULT_STATUS_FILE = os.getenv(
    "BITSTAR_POOL_LEDGER_BACKUP_STATUS_FILE",
    "/var/lib/bitstar/pool-ledger-backup-status.json",
)
DEFAULT_RETENTION_DAYS = int(os.getenv("BITSTAR_POOL_LEDGER_BACKUP_RETENTION_DAYS", "14"))
COUNTER_KEYS = (
    "submitted_shares",
    "accepted_shares",
    "candidate_blocks",
    "accepted_blocks",
    "rejected_blocks",
    "failed_blocks",
)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def compact_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def connect_readonly(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {str(row["name"]) for row in rows}


def verify_database(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"ledger database not found: {path}")

    with contextlib.closing(connect_readonly(path)) as conn:
        quick_check = conn.execute("PRAGMA quick_check").fetchone()[0]
        if quick_check != "ok":
            raise RuntimeError(f"SQLite quick_check failed: {quick_check}")

        tables = table_names(conn)
        totals: dict[str, int] = {}
        if "dry_run_totals" in tables:
            rows = conn.execute("SELECT counter, value FROM dry_run_totals ORDER BY counter")
            totals = {str(row["counter"]): int(row["value"]) for row in rows}

        worker_count = 0
        if "dry_run_workers" in tables:
            worker_count = int(conn.execute("SELECT COUNT(*) FROM dry_run_workers").fetchone()[0])

        meta: dict[str, str] = {}
        if "dry_run_meta" in tables:
            rows = conn.execute("SELECT key, value FROM dry_run_meta ORDER BY key")
            meta = {str(row["key"]): str(row["value"]) for row in rows}

    return {
        "quick_check": "ok",
        "tables": sorted(tables),
        "worker_count": worker_count,
        "totals": {key: int(totals.get(key, 0)) for key in COUNTER_KEYS},
        "meta": {
            "schema_version": meta.get("schema_version"),
            "mode": meta.get("mode"),
            "storage": meta.get("storage"),
            "window_started_at": meta.get("window_started_at"),
            "window_updated_at": meta.get("window_updated_at"),
        },
    }


def backup_name() -> str:
    return f"pool-dry-run-ledger-{compact_stamp()}.sqlite3"


def backup_database(source: Path, backup_dir: Path) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"ledger database not found: {source}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    final_path = backup_dir / backup_name()
    fd, tmp_name = tempfile.mkstemp(
        prefix=final_path.stem + "-",
        suffix=".tmp",
        dir=str(backup_dir),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)

    try:
        with contextlib.closing(connect_readonly(source)) as src:
            with contextlib.closing(sqlite3.connect(tmp_path)) as dst:
                src.backup(dst)
        verify_database(tmp_path)
        tmp_path.replace(final_path)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            tmp_path.unlink()
        raise

    return final_path


def backup_files(backup_dir: Path) -> list[Path]:
    return sorted(backup_dir.glob("pool-dry-run-ledger-*.sqlite3"))


def latest_backup(backup_dir: Path) -> Path:
    backups = backup_files(backup_dir)
    if not backups:
        raise FileNotFoundError(f"no ledger backups found in {backup_dir}")
    return backups[-1]


def prune_backups(backup_dir: Path, retention_days: int) -> list[str]:
    if retention_days <= 0:
        return []
    cutoff = time.time() - retention_days * 86400
    removed: list[str] = []
    for path in backup_files(backup_dir):
        if path.stat().st_mtime >= cutoff:
            continue
        path.unlink()
        removed.append(path.name)
        metadata_path = path.with_suffix(path.suffix + ".json")
        with contextlib.suppress(FileNotFoundError):
            metadata_path.unlink()
    return removed


def backup_summary(path: Path, source: Path, retention_days: int, pruned: list[str]) -> dict[str, Any]:
    verification = verify_database(path)
    summary = {
        "schema_version": 1,
        "created_at": utc_now(),
        "source_file": source.name,
        "backup_file": path.name,
        "backup_size_bytes": path.stat().st_size,
        "backup_sha256": sha256_file(path),
        "retention_days": retention_days,
        "pruned_backups": pruned,
        "verification": verification,
    }
    write_json_atomic(path.with_suffix(path.suffix + ".json"), summary)
    return summary


def write_backup_status(status_file: Path, event: dict[str, Any]) -> None:
    status = read_json(status_file)
    status["schema_version"] = 1
    status["updated_at"] = utc_now()

    if event.get("event") == "backup":
        status["last_backup_at"] = event["created_at"]
        status["last_backup_file"] = event["backup_file"]
        status["last_backup_size_bytes"] = event["backup_size_bytes"]
        status["last_backup_sha256"] = event["backup_sha256"]
        status["last_verify_ok"] = True
        status["retention_days"] = event["retention_days"]
        status["backup_count"] = event["backup_count"]
        status["verified_totals"] = event["verification"].get("totals", {})
        status["verified_worker_count"] = event["verification"].get("worker_count", 0)
    elif event.get("event") == "restore_drill":
        status["last_restore_drill_at"] = event["created_at"]
        status["last_restore_drill_file"] = event["backup_file"]
        status["last_restore_drill_ok"] = True
        status["last_restore_drill_totals"] = event["verification"].get("totals", {})

    write_json_atomic(status_file, status)


def command_backup(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.db)
    backup_dir = Path(args.backup_dir)
    status_file = Path(args.status_file)
    backup_path = backup_database(source, backup_dir)
    pruned = prune_backups(backup_dir, args.retention_days)
    summary = backup_summary(backup_path, source, args.retention_days, pruned)
    summary["event"] = "backup"
    summary["backup_count"] = len(backup_files(backup_dir))
    write_backup_status(status_file, summary)
    return summary


def command_verify(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.path)
    return {
        "event": "verify",
        "created_at": utc_now(),
        "backup_file": path.name,
        "backup_size_bytes": path.stat().st_size,
        "backup_sha256": sha256_file(path),
        "verification": verify_database(path),
    }


def command_restore_drill(args: argparse.Namespace) -> dict[str, Any]:
    backup_dir = Path(args.backup_dir)
    backup_path = Path(args.backup) if args.backup else latest_backup(backup_dir)
    drill_dir = Path(args.drill_dir) if args.drill_dir else Path(tempfile.mkdtemp(prefix="bitstar-ledger-drill-"))
    drill_dir.mkdir(parents=True, exist_ok=True)
    drill_path = drill_dir / f"restore-drill-{backup_path.name}"

    shutil.copy2(backup_path, drill_path)
    verification = verify_database(drill_path)
    if not args.keep_drill_copy:
        with contextlib.suppress(FileNotFoundError):
            drill_path.unlink()
        with contextlib.suppress(OSError):
            drill_dir.rmdir()

    summary = {
        "schema_version": 1,
        "event": "restore_drill",
        "created_at": utc_now(),
        "backup_file": backup_path.name,
        "backup_size_bytes": backup_path.stat().st_size,
        "backup_sha256": sha256_file(backup_path),
        "restored_to": str(drill_path) if args.keep_drill_copy else "temporary copy removed after verification",
        "verification": verification,
    }
    write_backup_status(Path(args.status_file), summary)
    return summary


def print_result(data: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    print(f"{data.get('event', 'ok')}: {data.get('backup_file', data.get('created_at', 'ok'))}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Back up and verify the BitStar pool dry-run SQLite ledger.")
    parser.add_argument("--json", action="store_true", help="print JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup", help="create and verify an online SQLite backup")
    backup.add_argument("--db", default=DEFAULT_LEDGER_DB)
    backup.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR)
    backup.add_argument("--status-file", default=DEFAULT_STATUS_FILE)
    backup.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)

    verify = subparsers.add_parser("verify", help="verify a backup or ledger database")
    verify.add_argument("path")

    drill = subparsers.add_parser("restore-drill", help="copy the latest backup to a temp database and verify it")
    drill.add_argument("--backup", default="")
    drill.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR)
    drill.add_argument("--drill-dir", default="")
    drill.add_argument("--status-file", default=DEFAULT_STATUS_FILE)
    drill.add_argument("--keep-drill-copy", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "backup":
            result = command_backup(args)
        elif args.command == "verify":
            result = command_verify(args)
        elif args.command == "restore-drill":
            result = command_restore_drill(args)
        else:
            raise RuntimeError(f"unknown command: {args.command}")
        print_result(result, args.json)
        return 0
    except Exception as exc:
        error = {"event": "error", "created_at": utc_now(), "error": str(exc)}
        print_result(error, args.json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
