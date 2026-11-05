"""Campus Customs database paths.

MCP tools and the backend open the working copy only. The original file is
the reset source and is never opened for writes.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ORIGINAL_DB = DATA_DIR / "campus_customs.db"
WORKING_DB = DATA_DIR / "campus_customs_new.db"


def working_db_path() -> Path:
    raw = os.environ.get("CAMPUS_CUSTOMS_DB", "").strip()
    path = Path(raw) if raw else WORKING_DB
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path == ORIGINAL_DB.resolve():
        raise RuntimeError(
            "CAMPUS_CUSTOMS_DB points at campus_customs.db. "
            "Tools must update data/campus_customs_new.db."
        )
    return path


def connect() -> sqlite3.Connection:
    """Open the working copy for reads and ticket updates."""
    path = working_db_path()
    if not path.exists():
        raise FileNotFoundError(f"Working database is missing: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def reset_working_copy() -> Path:
    """Replace the working copy with a fresh copy of the original file."""
    if not ORIGINAL_DB.exists():
        raise FileNotFoundError(ORIGINAL_DB)
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    return WORKING_DB
