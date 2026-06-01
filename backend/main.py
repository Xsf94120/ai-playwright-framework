from __future__ import annotations

import fastapi
from fastapi.middleware.cors import CORSMiddleware

from app.db import SessionLocal, init_db
from app.routers import auth, configs, projects, runs, suites
from app.seed import seed_initial_data

app = fastapi.FastAPI(title="AI Playwright 平台 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(configs.router)
app.include_router(suites.router)
app.include_router(runs.router)
