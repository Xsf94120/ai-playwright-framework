from __future__ import annotations

import os
import sys
from pathlib import Path

# `backend/` is now the self-contained service root: it holds both the FastAPI
# app (`app/`) and the fully integrated engine package (`ai_playwright/`).
BACKEND_ROOT = Path(__file__).resolve().parents[1]

# The engine package lives inside the backend service.
ENGINE_ROOT = BACKEND_ROOT
ENGINE_PACKAGE = BACKEND_ROOT / "ai_playwright"
ENGINE_TEMPLATES = ENGINE_PACKAGE / "templates"

# Backwards-compatible alias used across services/seed.
REPO_ROOT = BACKEND_ROOT

# All platform-managed runtime artifacts live under backend/.platform (gitignored).
DATA_DIR = BACKEND_ROOT / ".platform"
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
PYTHON_BIN = sys.executable or "python"
