"""Database calls must not run on Qt's UI thread."""

import threading
import time

from PySide6.QtWidgets import QApplication

from ui.workers import DatabaseTask, run_database_task


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
