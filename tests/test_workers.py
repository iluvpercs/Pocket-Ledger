"""Database calls must not run on Qt's UI thread."""

import threading
import time

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from ui.workers import (
    DatabaseTask,
    active_database_task_count,
    run_database_task,
    wait_for_all_database_tasks,
)


def _wait(task, seconds=5):
    deadline = time.monotonic() + seconds
    while task.isRunning() and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.005)
    # Signal deliveries are queued on the UI thread; drain them after the
    # worker has stopped before asserting on the collected results.
    for _ in range(5):
        QApplication.processEvents()
        time.sleep(0.01)


def test_database_task_runs_in_another_thread(qapp):
    ui_thread = threading.get_ident()

    def work():
        return threading.get_ident() != ui_thread

    task = DatabaseTask(work)
    results = []
    task.succeeded.connect(results.append)
    task.start()
    _wait(task)

    assert results == [True]


def test_database_task_reports_failures_without_crashing(qapp):
    def broken():
        raise ValueError("bad database call")

    task = DatabaseTask(broken)
    errors = []
    task.failed.connect(errors.append)
    task.start()
    _wait(task)

    assert len(errors) == 1
    assert "bad database call" in errors[0]


def test_run_database_task_calls_success_handler(qapp, temp_database):
    import database

    results = []
    task = run_database_task(
        qapp,
        lambda: [dict(row) for row in database.get_all_transactions()],
        on_success=results.append,
    )
    _wait(task)
    assert results == [[]]


def test_direct_database_task_is_registered(qapp, temp_database):
    before = active_database_task_count()
    task = DatabaseTask(lambda: "direct")

    assert active_database_task_count() == before + 1

    task.start()
    wait_for_all_database_tasks(timeout=5.0)
    assert active_database_task_count() == before


def test_wait_for_all_database_tasks_joins_completed_work(qapp, temp_database):
    results = []
    run_database_task(qapp, lambda: "done", on_success=results.append)

    wait_for_all_database_tasks(timeout=5.0)

    assert results == ["done"]
    assert active_database_task_count() == 0


def test_wait_for_all_database_tasks_uses_qthread_wait(qapp, temp_database, monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def blocked():
        started.set()
        release.wait(2.0)
        return "late"

    waited = []
    original_wait = QThread.wait

    def spy_wait(self, msecs=None):
        waited.append(msecs)
        if msecs is None:
            return original_wait(self)
        return original_wait(self, msecs)

    monkeypatch.setattr(QThread, "wait", spy_wait)
    run_database_task(qapp, blocked)
    assert started.wait(1.0)

    try:
        with pytest.raises(TimeoutError, match="still running"):
            wait_for_all_database_tasks(timeout=0.05)
    finally:
        release.set()
        wait_for_all_database_tasks(timeout=5.0)

    assert waited, "wait_for_all_database_tasks() must call QThread.wait()"


def test_wait_for_all_database_tasks_reports_timeout(qapp, temp_database):
    started = threading.Event()
    release = threading.Event()

    def blocked():
        started.set()
        release.wait(2.0)
        return "late"

    task = run_database_task(qapp, blocked)
    assert started.wait(1.0)

    try:
        with pytest.raises(TimeoutError, match="still running"):
            wait_for_all_database_tasks(timeout=0.05)
        assert task.isRunning()
        assert not task._pocket_ledger_finalized
        assert active_database_task_count() >= 1
    finally:
        release.set()
        wait_for_all_database_tasks(timeout=5.0)

    assert active_database_task_count() == 0
