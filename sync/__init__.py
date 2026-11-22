"""Building blocks for local-first synchronisation.

Nothing in this package talks to the network yet. Milestone 1 only prepares
the local database so that a future phone or second computer can ask for
"everything that changed since change number N".

Keeping these helpers in their own package means the FastAPI server and the
Flutter client can reuse the same rules later without changing the desktop UI.
"""
