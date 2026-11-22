"""CSV statement import for the desktop app (Milestone 2).

The modules here contain no user-interface code:

* ``csv_parser`` turns a bank CSV into a preview-friendly row model;
* ``dedupe`` builds stable import hashes and compares them with the database;
* ``service`` ties parsing, user edits and the all-or-nothing commit together.
"""
