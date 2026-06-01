from __future__ import annotations

import os
from pathlib import Path

# Repo root = parent of the `backend` directory.
REPO_ROOT = Path(__file__).resolve().parents[2]

# All platform-managed runtime artifacts live under .platform (gitignored).
DATA_DIR = REPO_ROOT / ".platform"
RUNS_DIR = DATA_DIR / "runs"
DB_PATH = DATA_DIR / "platform.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Secret for signing JWTs. In production set PLATFORM_JWT_SECRET.
JWT_SECRET = os.environ.get("PLATFORM_JWT_SECRET", "ai-playwright-platform-dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7

# Python interpreter used to launch the engine subprocess.
import sys  # noqa: E402

PYTHON_BIN = sys.executable or "python"
