from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Project, Run, Suite

router = APIRouter(prefix="/stats", tags=["stats"], dependencies=[Depends(get_current_user)])


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    project_count = db.query(func.count(Project.id)).scalar() or 0
    suite_count = db.query(func.count(Suite.id)).scalar() or 0
    run_count = db.query(func.count(Run.id)).scalar() or 0

    passed = db.query(func.count(Run.id)).filter(Run.status == "passed").scalar() or 0
    failed = db.query(func.count(Run.id)).filter(Run.status == "failed").scalar() or 0
    running = (
        db.query(func.count(Run.id))
        .filter(Run.status.in_(["pending", "running"]))
        .scalar()
        or 0
    )
    finished = passed + failed
    pass_rate = round(passed / finished * 100, 1) if finished else 0.0

    # Last 7 days trend (passed/failed per day).
    today = datetime.utcnow().date()
    trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        base = db.query(func.count(Run.id)).filter(
            Run.created_at >= day_start, Run.created_at < day_end
        )
        d_passed = base.filter(Run.status == "passed").scalar() or 0
        d_failed = base.filter(Run.status == "failed").scalar() or 0
        trend.append(
            {"date": day.strftime("%m-%d"), "passed": d_passed, "failed": d_failed}
        )

    recent = db.query(Run).order_by(Run.created_at.desc()).limit(8).all()
    recent_runs = [
        {
            "id": r.id,
            "project_key": r.project_key,
            "suite_name": r.suite_name,
            "kind": r.kind,
            "status": r.status,
            "env": r.env,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent
    ]

    return {
        "projects": project_count,
        "suites": suite_count,
        "runs": run_count,
        "passed": passed,
        "failed": failed,
        "running": running,
        "pass_rate": pass_rate,
        "trend": trend,
        "recent_runs": recent_runs,
    }
