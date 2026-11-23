"""Identify this computer inside the Pocket Ledger database.

Every database gets one random ``device_id`` the first time it is upgraded.
The id is stored in the ``app_meta`` table, so it stays the same after the app
is closed and reopened. Later, sync can use it to answer "which device made
this change?" without relying on a computer name (which can be duplicated).
"""

import platform
import uuid

# Used when the operating system does not give us a computer name.
DEFAULT_DEVICE_NAME = "Windows Desktop"

# The default INR account must have the same UUID on every device. Deriving it
# from a fixed name means two devices that migrate independently create the
# same account instead of two look-alike accounts that later collide in sync.
DEFAULT_ACCOUNT_UUID = str(
    uuid.uuid5(uuid.NAMESPACE_URL, "pocket-ledger:account:default-inr")
)
DEFAULT_ACCOUNT_NAME = "Default INR account"


def get_meta(connection, key, default=None):
    """Read one value from app_meta, or return ``default`` when it is missing."""
    row = connection.execute(
        "SELECT value FROM app_meta WHERE key = ?", (str(key),)
    ).fetchone()
    return row[0] if row is not None else default


def set_meta(connection, key, value):
    """Insert or replace one app_meta value."""
    connection.execute(
        """
        INSERT INTO app_meta (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (str(key), str(value)),
    )


def get_or_create_device_id(connection):
    """Return this database's device id, creating it on first use.

    ``uuid4`` produces a long random value, for example
    ``"9f1c4d7e-..."``. Two computers generating ids at the same moment will
    not collide, which is exactly what a future sync needs.
    """
    existing = get_meta(connection, "local_device_id")
    if existing:
        return existing

    new_id = str(uuid.uuid4())
    set_meta(connection, "local_device_id", new_id)
    set_meta(
        connection,
        "device_name",
        get_meta(connection, "device_name") or platform.node() or DEFAULT_DEVICE_NAME,
    )
    set_meta(connection, "device_platform", "windows")
    return new_id


def get_device_name(connection):
    """Return the friendly name shown to a future pairing screen."""
    return get_meta(connection, "device_name") or DEFAULT_DEVICE_NAME
