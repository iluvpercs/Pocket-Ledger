"""Controlled recovery for the five accidentally soft-deleted transactions.

This script never writes to the database path passed on the command line. It
makes a separate working copy with SQLite's backup API, validates that copy,
restores the five rows inside one ``BEGIN IMMEDIATE`` transaction, appends five
explicit recovery events, and prints a JSON report.

The canonical live database is always refused. Promotion of the working copy
is a separate, manually approved operation and is not performed here.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from sync.identity import get_meta  # noqa: E402
from sync.store import (  # noqa: E402
    PAYLOAD_FIELDS,
    append_change,
    transaction_payload,
    utc_now_ms,
)

EXPECTED_TRANSACTIONS = (
    {
        "id": 3,
        "uuid": "0cf3763b-7e15-4f51-963c-303b12713dc3",
        "transaction_type": "income",
        "amount": 24000.0,
        "transaction_date": "2026-11-22",
        "category": "Salary",
    },
    {
        "id": 4,
        "uuid": "fcbf555e-5cc6-4cff-83b9-5620e10b6ca8",
        "transaction_type": "expense",
        "amount": 500.0,
        "transaction_date": "2026-11-22",
        "category": "Food",
    },
    {
        "id": 5,
        "uuid": "30b91ff7-aa11-4c78-8d47-e540047fd267",
        "transaction_type": "expense",
        "amount": 300.0,
        "transaction_date": "2026-11-22",
        "category": "Transport",
    },
    {
        "id": 6,
        "uuid": "233b3af1-2c69-42a4-a692-762cdb8545b5",
        "transaction_type": "expense",
        "amount": 1000.0,
        "transaction_date": "2026-11-22",
        "category": "Entertainment",
    },
    {
        "id": 7,
        "uuid": "278723e6-0e0e-4d19-83b5-6e6ff59e6691",
        "transaction_type": "income",
        "amount": 20000.0,
        "transaction_date": "2026-11-22",
        "category": "salary",
    },
)

EXPECTED_IDS = tuple(row["id"] for row in EXPECTED_TRANSACTIONS)
EXPECTED_UUIDS = tuple(row["uuid"] for row in EXPECTED_TRANSACTIONS)
ORIGINAL_EVENT_COUNT = 10
RECOVERY_EVENT_COUNT = len(EXPECTED_TRANSACTIONS)
BASE_REVISION = 2
RECOVERY_REVISION = 3
REQUIRED_SCHEMA_VERSION = 3
REQUIRED_COLUMNS = frozenset(PAYLOAD_FIELDS) | {"id", "sync_state"}
CHANGED_COLUMNS = frozenset({"deleted_at_ms", "updated_at_ms", "revision"})


class RecoveryError(RuntimeError):
    """Base class for controlled recovery failures."""


class RecoverySafetyError(RecoveryError):
    """Raised when a safety precondition refuses the operation."""


class RecoveryValidationError(RecoveryError):
    """Raised when source data does not match the approved recovery state."""


def _canonical(path):
    return database._canonical_path(path)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _is_same_file(left, right):
    """True when two paths resolve to the same underlying file/inode."""
    try:
        return left.is_file() and right.is_file() and os.path.samefile(left, right)
    except OSError:
        return False


def _reserve_working_copy(path):
    """Atomically create an empty output file, refusing to replace an existing one."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as error:
        raise RecoverySafetyError(
            f"Refusing to overwrite an existing working copy at {path}."
        ) from error
    os.close(descriptor)


def _rows(connection, sql, parameters=()):
    return [dict(row) for row in connection.execute(sql, parameters)]


def _table_columns(connection, table):
    return {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})")
    }


def _validate_schema(connection):
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version >= 4:
        raise RecoveryValidationError(
            f"This database is schema version {version}. The soft-delete "
            "recovery script is frozen at schema 3 and refuses to run on "
            "schema 4 or later. Use a separate v3 copy if recovery is still "
            "required."
        )
    if version != REQUIRED_SCHEMA_VERSION:
        raise RecoveryValidationError(
            f"Expected schema version {REQUIRED_SCHEMA_VERSION}, found {version}. "
            "This script does not run migrations."
        )

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    required_tables = {"transactions", "sync_changes", "app_meta"}
    missing_tables = sorted(required_tables - tables)
    if missing_tables:
        raise RecoveryValidationError(
            "Missing required tables: " + ", ".join(missing_tables)
        )

    columns = _table_columns(connection, "transactions")
    missing_columns = sorted(REQUIRED_COLUMNS - columns)
    if missing_columns:
        raise RecoveryValidationError(
            "transactions is missing required columns: "
            + ", ".join(missing_columns)
        )

    change_columns = _table_columns(connection, "sync_changes")
    required_change_columns = {
        "seq",
        "entity_type",
        "entity_uuid",
        "operation",
        "base_revision",
        "new_revision",
        "payload",
        "origin_device_id",
        "recorded_at_ms",
    }
    missing_change_columns = sorted(required_change_columns - change_columns)
    if missing_change_columns:
        raise RecoveryValidationError(
            "sync_changes is missing required columns: "
            + ", ".join(missing_change_columns)
        )

    meta_columns = _table_columns(connection, "app_meta")
    if not {"key", "value"} <= meta_columns:
        raise RecoveryValidationError("app_meta must have key and value columns.")


def _make_working_copy(source_path, requested_working_copy):
    if requested_working_copy is not None:
        working_copy = _canonical(requested_working_copy)
        if working_copy == source_path:
            raise RecoverySafetyError(
                "The working copy must be a different path from the source."
            )
        working_copy.parent.mkdir(parents=True, exist_ok=True)
        _reserve_working_copy(working_copy)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = 0
        while True:
            name = f"{source_path.stem}_recovered_{stamp}.db"
            if suffix:
                name = f"{source_path.stem}_recovered_{stamp}_{suffix}.db"
            candidate = _canonical(source_path.with_name(name))
            try:
                _reserve_working_copy(candidate)
            except RecoverySafetyError:
                suffix += 1
                continue
            working_copy = candidate
            break

    # immutable=1 means SQLite never creates WAL/SHM files beside the source.
    source = None
    target = None
    try:
        source = sqlite3.connect(
            f"file:{source_path.as_posix()}?mode=ro&immutable=1", uri=True
        )
        target = sqlite3.connect(working_copy)
        source.backup(target)
    except BaseException:
        if target is not None:
            target.close()
        if source is not None:
            source.close()
        try:
            working_copy.unlink()
        except FileNotFoundError:
            pass
        raise
    else:
        target.close()
        source.close()
    return working_copy


def _validate_preconditions(connection, rows, events):
    if len(rows) != RECOVERY_EVENT_COUNT:
        raise RecoveryValidationError(
            f"Expected {RECOVERY_EVENT_COUNT} transactions, found {len(rows)}."
        )

    ids = tuple(row["id"] for row in rows)
    uuids = tuple(row["uuid"] for row in rows)
    if ids != EXPECTED_IDS:
        raise RecoveryValidationError(
            f"Unexpected transaction ids: expected {EXPECTED_IDS}, found {ids}."
        )
    if uuids != EXPECTED_UUIDS:
        raise RecoveryValidationError(
            "Unexpected transaction UUIDs. Recovery requires the original five "
            "identifiers so sync clients do not create duplicates."
        )

    distinct_uuids = connection.execute(
        "SELECT COUNT(DISTINCT uuid) FROM transactions"
    ).fetchone()[0]
    if distinct_uuids != RECOVERY_EVENT_COUNT:
        raise RecoveryValidationError(
            f"Expected {RECOVERY_EVENT_COUNT} distinct UUIDs, found {distinct_uuids}."
        )

    by_id = {row["id"]: row for row in rows}
    for expected in EXPECTED_TRANSACTIONS:
        row = by_id[expected["id"]]
        if row["uuid"] != expected["uuid"]:
            raise RecoveryValidationError(
                f"Unexpected uuid for id {expected['id']}: "
                f"expected {expected['uuid']}, found {row['uuid']}."
            )
        for field in ("transaction_type", "amount", "transaction_date", "category"):
            if row[field] != expected[field]:
                raise RecoveryValidationError(
                    f"Unexpected {field} for id {expected['id']}: "
                    f"expected {expected[field]!r}, found {row[field]!r}."
                )
        if row["deleted_at_ms"] is None:
            raise RecoveryValidationError(
                f"Transaction id {expected['id']} is already active; refusing recovery."
            )
        if row["revision"] != BASE_REVISION:
            raise RecoveryValidationError(
                f"Unexpected revision for id {expected['id']}: "
                f"expected {BASE_REVISION}, found {row['revision']}."
            )

    matching_recovery_events = [
        event
        for event in events
        if event["operation"] == "update"
        and event["base_revision"] == BASE_REVISION
        and event["new_revision"] == RECOVERY_REVISION
        and event["entity_uuid"] in EXPECTED_UUIDS
    ]
    if matching_recovery_events:
        raise RecoveryValidationError(
            "Matching recovery update events already exist at seq "
            + ", ".join(str(event["seq"]) for event in matching_recovery_events)
            + "; refusing to append duplicates."
        )

    if len(events) != ORIGINAL_EVENT_COUNT:
        raise RecoveryValidationError(
            f"Expected {ORIGINAL_EVENT_COUNT} original sync events, found {len(events)}."
        )
    seqs = tuple(event["seq"] for event in events)
    if seqs != tuple(range(1, ORIGINAL_EVENT_COUNT + 1)):
        raise RecoveryValidationError(
            f"Unexpected sync event sequence: {seqs}. Expected 1..{ORIGINAL_EVENT_COUNT}."
        )

    insert_events = events[:RECOVERY_EVENT_COUNT]
    delete_events = events[RECOVERY_EVENT_COUNT:]

    if tuple(event["entity_uuid"] for event in insert_events) != EXPECTED_UUIDS:
        raise RecoveryValidationError(
            "Insert sync events seq 1-5 are not in the expected UUID order."
        )

    delete_uuids = tuple(event["entity_uuid"] for event in delete_events)
    if (
        sorted(delete_uuids) != sorted(EXPECTED_UUIDS)
        or len(set(delete_uuids)) != RECOVERY_EVENT_COUNT
    ):
        raise RecoveryValidationError(
            "Delete sync events seq 6-10 must contain each expected UUID exactly once, "
            "in any order."
        )

    for event in insert_events:
        if (
            event["operation"] != "insert"
            or event["base_revision"] is not None
            or event["new_revision"] != BASE_REVISION - 1
        ):
            raise RecoveryValidationError(
                f"Sync event seq {event['seq']} is not a valid initial insert event."
            )

    for event in delete_events:
        if (
            event["operation"] != "delete"
            or event["base_revision"] != BASE_REVISION - 1
            or event["new_revision"] != BASE_REVISION
        ):
            raise RecoveryValidationError(
                f"Sync event seq {event['seq']} is not a valid soft-delete event."
            )


def _verify_final_state(
    connection,
    before_rows,
    before_events,
    recovery_at_ms,
    recovery_seqs,
    device_id,
):
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RecoveryValidationError(f"SQLite integrity check failed: {integrity}")

    rows = _rows(connection, "SELECT * FROM transactions ORDER BY id")
    if len(rows) != RECOVERY_EVENT_COUNT:
        raise RecoveryValidationError(
            f"Final state has {len(rows)} transactions, expected "
            f"{RECOVERY_EVENT_COUNT}."
        )
    if tuple(row["id"] for row in rows) != EXPECTED_IDS:
        raise RecoveryValidationError("Final transaction ids do not match expectations.")
    if tuple(row["uuid"] for row in rows) != EXPECTED_UUIDS:
        raise RecoveryValidationError("Final transaction UUIDs do not match expectations.")

    distinct_uuids = connection.execute(
        "SELECT COUNT(DISTINCT uuid) FROM transactions"
    ).fetchone()[0]
    if distinct_uuids != RECOVERY_EVENT_COUNT:
        raise RecoveryValidationError(
            f"Final state has {distinct_uuids} distinct UUIDs, expected "
            f"{RECOVERY_EVENT_COUNT}."
        )

    active = connection.execute(
        "SELECT COUNT(*) FROM transactions WHERE deleted_at_ms IS NULL"
    ).fetchone()[0]
    deleted = connection.execute(
        "SELECT COUNT(*) FROM transactions WHERE deleted_at_ms IS NOT NULL"
    ).fetchone()[0]
    if active != RECOVERY_EVENT_COUNT or deleted != 0:
        raise RecoveryValidationError(
            f"Final state has {active} active and {deleted} deleted transactions."
        )

    by_id = {row["id"]: row for row in rows}
    for expected in EXPECTED_TRANSACTIONS:
        row = by_id[expected["id"]]
        before = before_rows[expected["id"]]
        if row["deleted_at_ms"] is not None:
            raise RecoveryValidationError(
                f"Transaction id {expected['id']} was not restored to active state."
            )
        if row["revision"] != RECOVERY_REVISION:
            raise RecoveryValidationError(
                f"Transaction id {expected['id']} has revision {row['revision']}, "
                f"expected {RECOVERY_REVISION}."
            )
        if row["updated_at_ms"] != recovery_at_ms:
            raise RecoveryValidationError(
                f"Transaction id {expected['id']} has an unexpected updated_at_ms."
            )
        for column in sorted(set(row) - CHANGED_COLUMNS):
            if row[column] != before[column]:
                raise RecoveryValidationError(
                    f"Column {column} changed unexpectedly for id {expected['id']}."
                )

    events = _rows(connection, "SELECT * FROM sync_changes ORDER BY seq")
    expected_event_count = ORIGINAL_EVENT_COUNT + RECOVERY_EVENT_COUNT
    if len(events) != expected_event_count:
        raise RecoveryValidationError(
            f"Final log has {len(events)} sync events, expected {expected_event_count}."
        )

    events_by_seq = {event["seq"]: event for event in events}
    for seq, before in before_events.items():
        if events_by_seq.get(seq) != before:
            raise RecoveryValidationError(
                f"Original sync event seq {seq} was modified."
            )

    new_events = events[ORIGINAL_EVENT_COUNT:]
    new_seqs = tuple(event["seq"] for event in new_events)
    if new_seqs != tuple(recovery_seqs):
        raise RecoveryValidationError(
            f"Unexpected recovery event seqs: {new_seqs}."
        )

    for expected, event in zip(EXPECTED_TRANSACTIONS, new_events):
        if (
            event["entity_type"] != "transaction"
            or event["entity_uuid"] != expected["uuid"]
            or event["operation"] != "update"
            or event["base_revision"] != BASE_REVISION
            or event["new_revision"] != RECOVERY_REVISION
            or event["origin_device_id"] != device_id
            or event["recorded_at_ms"] != recovery_at_ms
        ):
            raise RecoveryValidationError(
                f"Recovery event seq {event['seq']} has unexpected metadata."
            )
        payload = json.loads(event["payload"])
        if payload["uuid"] != expected["uuid"]:
            raise RecoveryValidationError(
                f"Recovery event seq {event['seq']} has the wrong UUID."
            )
        if payload["deleted_at_ms"] is not None or payload["revision"] != RECOVERY_REVISION:
            raise RecoveryValidationError(
                f"Recovery event seq {event['seq']} is not an active snapshot."
            )
        if payload["updated_at_ms"] != recovery_at_ms:
            raise RecoveryValidationError(
                f"Recovery event seq {event['seq']} has an unexpected timestamp."
            )

        expected_payload = transaction_payload(by_id[expected["id"]])
        if (
            payload != expected_payload
            or event["payload"] != json.dumps(expected_payload, sort_keys=True)
        ):
            raise RecoveryValidationError(
                f"Recovery event seq {event['seq']} is not the complete "
                "transaction_payload() snapshot."
            )


def _assert_source_unchanged(source, expected_hash, cause=None):
    actual_hash = _sha256(source)
    if actual_hash == expected_hash:
        return actual_hash
    error = RecoveryError(
        "Source database hash changed during recovery; investigate before promotion."
    )
    if cause is not None:
        raise error from cause
    raise error


def recover_soft_deleted_transactions(
    source_path,
    *,
    confirm_recovery=False,
    working_copy=None,
    recovery_at_ms=None,
):
    """Recover the five transactions into a separate working copy.

    ``source_path`` is explicit and is never written to. ``confirm_recovery``
    must be True, and the canonical live database path is always refused.
    """
    source = _canonical(source_path)
    live = _canonical(database.LIVE_DB_PATH)
    if not source.is_file():
        raise RecoveryValidationError(f"Source database does not exist: {source}")
    source_hash_before = _sha256(source)
    source_hash_after = source_hash_before
    try:
        if source == live:
            raise RecoverySafetyError(
                f"Refusing to operate on the canonical live database at {source}."
            )
        if _is_same_file(source, live):
            raise RecoverySafetyError(
                "Refusing to operate on the canonical live database through the "
                f"hard-link alias at {source}."
            )
        if not confirm_recovery:
            raise RecoverySafetyError(
                "Recovery is not confirmed. Pass --confirm-recovery or "
                "confirm_recovery=True after reviewing the recovery plan."
            )

        working_copy = _make_working_copy(source, working_copy)
        working_copy_hash_before = _sha256(working_copy)

        connection = sqlite3.connect(working_copy)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")

        started = False
        try:
            _validate_schema(connection)
            rows = _rows(connection, "SELECT * FROM transactions ORDER BY id")
            events = _rows(connection, "SELECT * FROM sync_changes ORDER BY seq")
            before_rows = {row["id"]: row for row in rows}
            before_events = {event["seq"]: event for event in events}
            _validate_preconditions(connection, rows, events)

            device_id = get_meta(connection, "local_device_id")
            if not device_id:
                raise RecoveryValidationError(
                    "app_meta has no local_device_id; refusing to invent an origin."
                )

            if recovery_at_ms is None:
                recovery_at_ms = utc_now_ms()
            else:
                recovery_at_ms = int(recovery_at_ms)

            connection.execute("BEGIN IMMEDIATE")
            started = True

            recovery_seqs = []
            for expected in EXPECTED_TRANSACTIONS:
                cursor = connection.execute(
                    """
                    UPDATE transactions
                       SET deleted_at_ms = NULL,
                           updated_at_ms = ?,
                           revision = ?
                     WHERE id = ?
                       AND uuid = ?
                       AND deleted_at_ms IS NOT NULL
                       AND revision = ?
                    """,
                    (
                        recovery_at_ms,
                        RECOVERY_REVISION,
                        expected["id"],
                        expected["uuid"],
                        BASE_REVISION,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RecoveryValidationError(
                        f"Guarded update for id {expected['id']} affected "
                        f"{cursor.rowcount} rows."
                    )

                restored = connection.execute(
                    "SELECT * FROM transactions WHERE id = ? AND uuid = ?",
                    (expected["id"], expected["uuid"]),
                ).fetchone()
                seq = append_change(
                    connection,
                    entity_uuid=expected["uuid"],
                    operation="update",
                    payload=transaction_payload(restored),
                    origin_device_id=device_id,
                    base_revision=BASE_REVISION,
                    new_revision=RECOVERY_REVISION,
                    recorded_at_ms=recovery_at_ms,
                )
                recovery_seqs.append(int(seq))

            if recovery_seqs != list(
                range(
                    ORIGINAL_EVENT_COUNT + 1,
                    ORIGINAL_EVENT_COUNT + RECOVERY_EVENT_COUNT + 1,
                )
            ):
                raise RecoveryValidationError(
                    f"Expected recovery seqs 11..15, got {recovery_seqs}."
                )

            _verify_final_state(
                connection,
                before_rows,
                before_events,
                recovery_at_ms,
                recovery_seqs,
                device_id,
            )
            connection.commit()
            started = False
        except BaseException:
            if started:
                connection.rollback()
            raise
        finally:
            connection.close()

        working_copy_hash_after = _sha256(working_copy)
        report = {
            "status": "completed",
            "source_path": str(source),
            "source_sha256_before": source_hash_before,
            "source_sha256_after": source_hash_after,
            "source_unchanged": True,
            "working_copy_path": str(working_copy),
            "working_copy_sha256_before": working_copy_hash_before,
            "working_copy_sha256_after": working_copy_hash_after,
            "schema_version": REQUIRED_SCHEMA_VERSION,
            "integrity": "ok",
            "recovery_at_ms": recovery_at_ms,
            "origin_device_id": device_id,
            "transactions": {
                "before": len(rows),
                "after": len(rows),
                "active_before": sum(
                    row["deleted_at_ms"] is None for row in before_rows.values()
                ),
                "deleted_before": sum(
                    row["deleted_at_ms"] is not None for row in before_rows.values()
                ),
                "active_after": RECOVERY_EVENT_COUNT,
                "deleted_after": 0,
                "distinct_uuids_after": RECOVERY_EVENT_COUNT,
            },
            "sync_events": {
                "before": ORIGINAL_EVENT_COUNT,
                "after": ORIGINAL_EVENT_COUNT + RECOVERY_EVENT_COUNT,
                "original_events_preserved": True,
                "recovery_events_appended": RECOVERY_EVENT_COUNT,
                "recovery_event_seqs": recovery_seqs,
            },
        }
    except BaseException as error:
        _assert_source_unchanged(source, source_hash_before, cause=error)
        raise
    else:
        source_hash_after = _assert_source_unchanged(source, source_hash_before)
        report["source_sha256_after"] = source_hash_after
        return report


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Restore five soft-deleted transactions into a separate working copy. "
            "The live database is refused and is never overwritten."
        )
    )
    parser.add_argument(
        "database",
        help="Explicit source database path. There is no default path.",
    )
    parser.add_argument(
        "--confirm-recovery",
        action="store_true",
        help="Required confirmation that the recovery plan has been reviewed.",
    )
    parser.add_argument(
        "--working-copy",
        help="Optional explicit working-copy path; it must not already exist.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = recover_soft_deleted_transactions(
            args.database,
            confirm_recovery=args.confirm_recovery,
            working_copy=args.working_copy,
        )
    except RecoveryError as error:
        print(f"Recovery refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
