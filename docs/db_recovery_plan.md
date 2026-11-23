# Database recovery plan (prepared, not executed)

Status: **prepared only**. The live database has not been modified.

Sync-history decision: **preserve the original delete events and append five explicit recovery `update` events**. The earlier draft that removed `seq` 6–10 is superseded.

## Inputs

| Role | Path | SHA-256 |
|---|---|---|
| Live database (current, soft-deleted) | `data/pocket_ledger.db` | `53fe497e3a480d4d874d4767893ddeea87849f37ee3cc9a7acacd6dddf4225bc` |
| Known-good backup (active rows) | `data/backups/pocket_ledger_pre_milestone2_20261123_004428.db` | inspect read-only before use |
| Recovery copy of current live DB | `data/backups/pocket_ledger_recovery_prep_20261123_124917.db` | `06fc236e9010142110048c920bc0b586ac85348cf3670e05a10e502d7f19e5a0` |

All inspection uses `mode=ro&immutable=1` so no WAL/SHM sidecars are created beside the live file.

## Comparison result

Verified fields with no mismatches: `id`, `uuid`, `transaction_type`, `amount`, `transaction_date`, `category`.

| ID | UUID | Type | Amount | Date | Category | Backup `deleted_at_ms` | Live `deleted_at_ms` | Backup revision | Live revision |
|---:|---|---|---:|---|---|---:|---:|---:|---:|
| 3 | `0cf3763b-7e15-4f51-963c-303b12713dc3` | income | 24000.0 | 2026-11-22 | Salary | NULL | `1795379351449` | 1 | 2 |
| 4 | `fcbf555e-5cc6-4cff-83b9-5620e10b6ca8` | expense | 500.0 | 2026-11-22 | Food | NULL | `1795379349529` | 1 | 2 |
| 5 | `30b91ff7-aa11-4c78-8d47-e540047fd267` | expense | 300.0 | 2026-11-22 | Transport | NULL | `1795379344937` | 1 | 2 |
| 6 | `233b3af1-2c69-42a4-a692-762cdb8545b5` | expense | 1000.0 | 2026-11-22 | Entertainment | NULL | `1795379342578` | 1 | 2 |
| 7 | `278723e6-0e0e-4d19-83b5-6e6ff59e6691` | income | 20000.0 | 2026-11-22 | salary | NULL | `1795379347209` | 1 | 2 |

The backup has all five rows active (`deleted_at_ms IS NULL`, `revision = 1`). The live DB has all five soft-deleted (`revision = 2`) and five extra `delete` change-log rows (`seq` 6–10).

## Why not delete the old delete events?

`sync_changes` is append-only by design (`sync/store.py:1-9`). Removing `seq` 6–10 would rewrite history and would not correct a future Android device that had already consumed those events.

Retaining them and appending recovery events gives both fresh and already-synced clients a consistent result:

```text
insert (rev 1, active) -> delete (rev 2, tombstoned) -> update (rev 3, active)
```

## Exact proposed operations

Perform only on a **new working copy** of the recovery copy, inside one `BEGIN IMMEDIATE` transaction. Do not execute until separately approved.

Before the transaction, generate one UTC millisecond timestamp with `sync.store.utc_now_ms()` and call it `RECOVERY_AT_MS`. Use the same value for all five row updates and for all five recovery event `recorded_at_ms` values. Read the local device id from `app_meta['local_device_id']`.

### 1. Restore the five rows to active state

For each ID 3–7:

```sql
UPDATE transactions
   SET deleted_at_ms = NULL,
       updated_at_ms = :recovery_at_ms,
       revision = 3
 WHERE id = ?
   AND uuid = ?
   AND deleted_at_ms IS NOT NULL
   AND revision = 2;
```

Field changes per row:

| Field | Current value | Proposed value |
|---|---|---|
| `deleted_at_ms` | ID-specific delete timestamp listed above | `NULL` |
| `updated_at_ms` | same as the ID-specific delete timestamp | `RECOVERY_AT_MS` |
| `revision` | `2` | `3` |

Unchanged: `id`, `uuid`, `transaction_type`, `amount`, `transaction_date`, `category`, `description`, `created_at_ms`, `origin_device_id`, `last_modified_by`, `sync_state`, and all import fields.

### 2. Append five explicit recovery events

After each row update, call `sync.store.append_change()` with the updated row:

```python
append_change(
    connection,
    entity_uuid=row["uuid"],
    operation="update",
    payload=transaction_payload(row),
    origin_device_id=local_device_id,
    base_revision=2,
    new_revision=3,
    recorded_at_ms=RECOVERY_AT_MS,
)
```

`transaction_payload()` builds a full snapshot using `PAYLOAD_FIELDS`, including `deleted_at_ms: null` and `revision: 3`. The five new rows are expected to receive `seq` 11–15.

No `sync_changes` row is deleted, edited, or renumbered. The original `seq` 1–10 remain logically unchanged: all columns, including `payload`, are compared exactly. SQLite may rewrite file pages during the backup, so byte-for-byte file equality is not claimed.

### 3. Verify the working copy

Before any promotion:

- `PRAGMA user_version = 3`
- `PRAGMA integrity_check = 'ok'`
- 5 total transaction rows, 5 active, 0 soft-deleted.
- IDs 3–7 and their UUIDs, amounts, dates, categories and types still match the known-good backup.
- `COUNT(DISTINCT uuid) = 5`; no duplicate UUIDs.
- `COUNT(*) FROM transactions WHERE deleted_at_ms IS NULL = 5`.
- `sync_changes` has exactly 15 rows.
- `seq` 1–5 are the original insert events.
- `seq` 6–10 are the original delete events, unchanged.
- `seq` 11–15 are `operation = 'update'`, with `base_revision = 2`, `new_revision = 3`, and payload snapshots showing `deleted_at_ms = null` and `revision = 3`.
- SHA-256 recorded and compared.

### 4. Verify application visibility without touching live

Before promotion, start an offscreen app/test check with `POCKET_LEDGER_DB` pointed at the verified working copy and confirm:

- `database.get_all_transactions()` returns exactly IDs 3–7.
- The Transactions model shows exactly five rows.
- No duplicate UUIDs appear in the model or table.
- Dashboard active count is five, not zero.

### 5. Promote only after separate approval

Only with separate explicit approval:

1. Make a fresh pre-recovery backup of the current live DB.
2. Re-check the live SHA-256.
3. Atomically replace the live file with the verified working copy.
4. Re-run the read-only live verification.
5. Start the app normally and confirm the five transactions are visible with no duplicates.

Do not reuse this prepared copy as the final promoted file without a fresh hash check.

## Not performed

- No UPDATE/DELETE/INSERT has been run against the live DB.
- No backup was deleted or overwritten.
- No live restore or file replacement was performed.
- No app was launched against the live DB.
