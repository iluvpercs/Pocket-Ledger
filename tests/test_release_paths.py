"""Packaged-build data paths: portable beside the EXE, installed in user data."""

import os

import release_paths


def test_installed_data_dir_is_outside_the_installation(tmp_path):
    exe = tmp_path / "Programs" / "PocketLedger" / "PocketLedger.exe"
    data_dir = release_paths.default_data_dir(
        exe_path=exe, local_appdata=tmp_path / "AppData", portable=False
    )
    assert data_dir == tmp_path / "AppData" / "Pocket Ledger" / "data"
    assert not str(data_dir).lower().startswith(str(exe.parent).lower())


def test_portable_marker_keeps_data_beside_the_exe(tmp_path, monkeypatch):
    exe = tmp_path / "Portable" / "PocketLedger.exe"
    exe.parent.mkdir(parents=True)
    (exe.parent / release_paths.PORTABLE_MARKER).write_text("portable", encoding="utf-8")
    monkeypatch.setattr(release_paths, "is_frozen", lambda: True)

    assert release_paths.default_data_dir(
        exe_path=exe, local_appdata=tmp_path / "AppData"
    ) == exe.parent / "data"


def test_explicit_database_override_is_never_replaced(tmp_path, monkeypatch):
    custom = tmp_path / "custom.db"
    monkeypatch.setenv(release_paths.DB_PATH_ENV_VAR, str(custom))
    monkeypatch.setattr(release_paths, "is_frozen", lambda: True)

    result = release_paths.configure_environment(
        exe_path=tmp_path / "PocketLedger.exe", local_appdata=tmp_path / "AppData"
    )
    assert result is None
    assert os.environ[release_paths.DB_PATH_ENV_VAR] == str(custom)


def test_frozen_configure_creates_user_data_directory(tmp_path, monkeypatch):
    monkeypatch.delenv(release_paths.DB_PATH_ENV_VAR, raising=False)
    monkeypatch.setattr(release_paths, "is_frozen", lambda: True)

    path = release_paths.configure_environment(
        exe_path=tmp_path / "Programs" / "PocketLedger.exe",
        local_appdata=tmp_path / "AppData",
        portable=False,
    )
    assert path == tmp_path / "AppData" / "Pocket Ledger" / "data" / "pocket_ledger.db"
    assert path.parent.is_dir()
    assert os.environ[release_paths.DB_PATH_ENV_VAR] == str(path)
