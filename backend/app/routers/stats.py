from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Project, Run, Suite

router = APIRouter(prefix="/stats", tags=["stats"], dependencies=[Depends(get_current_user)])


def _duration_seconds(run: Run) -> float | None:
    if run.started_at and run.finished_at:
        return max(0.0, (run.finished_at - run.started_at).total_seconds())
    return None


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

    # Today's activity.
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_runs = (
        db.query(func.count(Run.id)).filter(Run.created_at >= today_start).scalar() or 0
    )

    # Average duration over finished runs (last 100).
    finished_runs = (
        db.query(Run)
        .filter(Run.status.in_(["passed", "failed"]))
        .order_by(Run.created_at.desc())
        .limit(100)
        .all()
    )
    durations = [d for r in finished_runs if (d := _duration_seconds(r)) is not None]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0

    # Last 7 days trend (passed/failed per day).
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

    # Per-project breakdown.
    projects = db.query(Project).all()
    project_breakdown = []
    for p in projects:
        p_passed = (
            db.query(func.count(Run.id))
            .filter(Run.project_id == p.id, Run.status == "passed")
            .scalar()
            or 0
        )
        p_failed = (
            db.query(func.count(Run.id))
            .filter(Run.project_id == p.id, Run.status == "failed")
            .scalar()
            or 0
        )
        p_total = (
            db.query(func.count(Run.id)).filter(Run.project_id == p.id).scalar() or 0
        )
        p_suites = (
            db.query(func.count(Suite.id)).filter(Suite.project_id == p.id).scalar() or 0
        )
        p_finished = p_passed + p_failed
        project_breakdown.append(
            {
                "id": p.id,
                "key": p.key,
                "name": p.name,
                "suites": p_suites,
                "runs": p_total,
                "passed": p_passed,
                "failed": p_failed,
                "pass_rate": round(p_passed / p_finished * 100, 1) if p_finished else 0.0,
            }
        )
    project_breakdown.sort(key=lambda x: x["runs"], reverse=True)

    # Top failing suites.
    fail_rows = (
        db.query(Run.suite_name, Run.project_key, func.count(Run.id).label("c"))
        .filter(Run.status == "failed", Run.suite_name != "")
        .group_by(Run.suite_name, Run.project_key)
        .order_by(func.count(Run.id).desc())
        .limit(5)
        .all()
    )
    top_failing = [
        {"suite_name": r[0], "project_key": r[1], "failures": r[2]} for r in fail_rows
    ]

    recent = db.query(Run).order_by(Run.created_at.desc()).limit(8).all()
    recent_runs = [
        {
            "id": r.id,
            "project_key": r.project_key,
            "suite_name": r.suite_name,
            "kind": r.kind,
            "status": r.status,
            "env": r.env,
            "duration": _duration_seconds(r),
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
        "today_runs": today_runs,
        "avg_duration": avg_duration,
        "trend": trend,
        "project_breakdown": project_breakdown,
        "top_failing": top_failing,
        "recent_runs": recent_runs,
    }
