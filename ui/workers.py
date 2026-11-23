"""Run database calls off the Qt UI thread.

Every public ``database.py`` function is synchronous. A 5,000-row read or a
large write would freeze the window if called on a button handler, so the UI
hands those calls to this small QThread wrapper instead.
"""

import time

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication

# Every DatabaseTask is registered here on construction. Tests wait on this
# registry so a late worker can never reconnect after the test DB path changes.
_live_tasks = []


def active_database_task_count():
    """Number of registered database tasks that have not been finalized."""
    return len(_live_tasks)


def _finalize_task(task):
    """Unregister and schedule deletion only after the QThread has stopped.

    ``deleteLater()`` is never called on a running QThread. The operation is
    idempotent so the ``finished`` signal and the explicit wait helper cannot
    schedule the same object twice.
    """
    if task.isRunning():
        return False
    if getattr(task, "_pocket_ledger_finalized", False):
        return True

    task._pocket_ledger_finalized = True
    if task in _live_tasks:
        _live_tasks.remove(task)
    task.deleteLater()
    return True


def wait_for_all_database_tasks(timeout=5.0):
    """Stop, reap and finalize every registered database task.

    ``QThread.wait()`` performs the deterministic thread join. Qt events are
    still processed between bounded waits so queued success/error callbacks can
    run on the UI thread. A timeout raises :class:`TimeoutError` instead of
    silently leaving a live thread behind.
    """
    deadline = time.monotonic() + timeout

    while True:
        QApplication.processEvents()
        pending = list(_live_tasks)
        if not pending:
            return

        if time.monotonic() >= deadline:
            running = [task for task in pending if task.isRunning()]
            names = ", ".join(
                getattr(task._function, "__name__", type(task._function).__name__)
                for task in running
            ) or "none"
            raise TimeoutError(
                f"{len(running)} database worker(s) still running after "
                f"{timeout:g}s ({names}); refusing to tear down the test database."
            )

        remaining_ms = max(1, int((deadline - time.monotonic()) * 1000))
        for task in pending:
            if task.isRunning():
                # Short bounded waits keep queued Qt signals deliverable.
                task.wait(min(remaining_ms, 20))
            QApplication.processEvents()
            _finalize_task(task)

        if not _live_tasks:
            QApplication.processEvents()
            return
        time.sleep(0.005)


class DatabaseTask(QThread):
    """Call one database function in a worker thread and report the result."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._pocket_ledger_finalized = False
        _live_tasks.append(self)
        self.finished.connect(lambda: _finalize_task(self))

    def run(self):
        try:
            result = self._function(*self._args, **self._kwargs)
        except Exception as error:  # reported to the UI, never swallowed
            self.failed.emit(f"{type(error).__name__}: {error}")
        else:
            self.succeeded.emit(result)


def run_database_task(
    owner, function, *args, on_success=None, on_error=None, **kwargs
):
    """Start a :class:`DatabaseTask` that stays alive until it finishes.

    ``owner`` is any QObject; the task is kept in a list on it so Python does
    not garbage-collect a running thread. The task is also registered globally
    by :class:`DatabaseTask` on construction, so tests can deterministically
    wait for it.
    """
    task = DatabaseTask(function, *args, **kwargs)

    tasks = getattr(owner, "_database_tasks", None)
    if tasks is None:
        tasks = []
        owner._database_tasks = tasks
    tasks.append(task)

    def cleanup():
        if task in tasks:
            tasks.remove(task)

    task.finished.connect(cleanup)

    def handle_success(result):
        if on_success is not None:
            on_success(result)

    def handle_error(message):
        if on_error is not None:
            on_error(message)

    task.succeeded.connect(handle_success)
    task.failed.connect(handle_error)
    task.start()
    return task
