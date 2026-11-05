"""Backend database handle. Ticket updates go to the working copy."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shop_db import (  # noqa: E402
    ORIGINAL_DB,
    WORKING_DB,
    connect,
    reset_working_copy,
    working_db_path,
)

__all__ = [
    "ORIGINAL_DB",
    "WORKING_DB",
    "connect",
    "reset_working_copy",
    "working_db_path",
]
