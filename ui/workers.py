"""Run database calls off the Qt UI thread.

Every public ``database.py`` function is synchronous. A 5,000-row read or a
large write would freeze the window if called from a button handler, so the UI
hands those calls to this small QThread wrapper instead.
"""

from PySide6.QtCore import QThread, Signal


class DatabaseTask(QThread):
    """Call one database function in a worker thread and report the result."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self._function = function
        self._args = args
        self._kwargs = kwargs

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
    not garbage-collect a running thread. Callbacks are invoked on the UI
    thread through Qt's signal/slot mechanism.
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
        task.deleteLater()

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
