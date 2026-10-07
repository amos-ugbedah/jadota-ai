"""
Shared in-memory position store.

Both `main.py` (which writes) and `analytics.py` (which reads) import from here
so they see the same list. In-memory is fine for the current demo flow; when
positions move to Postgres this file becomes a thin wrapper over a DB query.
"""

positions: list = []