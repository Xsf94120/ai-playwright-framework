from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.deps import get_current_user
from app.models import Project, Run, RunLog
from app.schemas import GenerateCreate, RunCreate, RunLogOut, RunOut
from app.security import decode_access_token
from app.services.runner import END_SENTINEL, execute_run, subscribe, unsubscribe

router = APIRouter(tags=["runs"])

# Authenticated REST endpoints.
secured = APIRouter(dependencies=[Depends(get_current_user)])


def _project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _validate_env(project: Project, env_name: str) -> None:
    """确保所选环境存在且已配置 BASE_URL，否则运行必然失败。"""
    env = next((e for e in project.environments if e.name == env_name), None)
    if env is None:
        raise HTTPException(
            status_code=400,
            detail=f"环境 {env_name} 不存在，请先在项目设置中创建该环境",
        )
    if not (env.base_url or "").strip():
        raise HTTPException(
            status_code=400,
            detail=f"环境 {env_name} 尚未配置 BASE_URL，请先在项目设置中补全",
        )


@secured.post("/runs", response_model=RunOut, status_code=201)
async def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> Run:
    project = _project_or_404(db, payload.project_id)
    _validate_env(project, payload.env)
    run = Run(
        project_id=project.id,
        project_key=project.key,
        suite_name=payload.suite_name,
        kind="run",
        status="pending",
        ai_mode=payload.ai_mode,
        env=payload.env,
        browser=payload.browser,
        headed=payload.headed,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    asyncio.create_task(execute_run(run.id))
    return run


@secured.post("/generate", response_model=RunOut, status_code=201)
async def create_generate(
    payload: GenerateCreate, db: Session = Depends(get_db)
) -> Run:
    project = _project_or_404(db, payload.project_id)
    _validate_env(project, payload.env)
    run = Run(
        project_id=project.id,
        project_key=project.key,
        suite_name=payload.suite_name,
        kind="generate",
        status="pending",
        env=payload.env,
        headed=payload.headed,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    asyncio.create_task(execute_run(run.id))
    return run


@secured.get("/runs", response_model=list[RunOut])
def list_runs(
    project_id: int | None = None,
    status: str | None = None,
    kind: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
) -> list[Run]:
    query = db.query(Run)
    if project_id is not None:
        query = query.filter(Run.project_id == project_id)
    if status:
        query = query.filter(Run.status == status)
    if kind:
        query = query.filter(Run.kind == kind)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Run.suite_name.ilike(like)) | (Run.project_key.ilike(like))
        )
    return query.order_by(Run.created_at.desc()).limit(200).all()


@secured.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)) -> Run:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    return run


@secured.post("/runs/{run_id}/rerun", response_model=RunOut, status_code=201)
async def rerun(run_id: int, db: Session = Depends(get_db)) -> Run:
    src = db.get(Run, run_id)
    if src is None:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    project = _project_or_404(db, src.project_id)
    run = Run(
        project_id=project.id,
        project_key=project.key,
        suite_name=src.suite_name,
        kind=src.kind,
        status="pending",
        ai_mode=src.ai_mode,
        env=src.env,
        browser=src.browser,
        headed=src.headed,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    asyncio.create_task(execute_run(run.id))
    return run


@secured.get("/runs/{run_id}/logs", response_model=list[RunLogOut])
def get_run_logs(run_id: int, db: Session = Depends(get_db)) -> list[RunLog]:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    return (
        db.query(RunLog)
        .filter(RunLog.run_id == run_id)
        .order_by(RunLog.seq.asc())
        .all()
    )


router.include_router(secured)


@router.websocket("/runs/{run_id}/stream")
async def stream_logs(websocket: WebSocket, run_id: int, token: str = "") -> None:
    username = decode_access_token(token) if token else None
    if not username:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    queue = subscribe(run_id)
    db = SessionLocal()
    try:
        # Replay history first so late subscribers see the full log.
        history = (
            db.query(RunLog)
            .filter(RunLog.run_id == run_id)
            .order_by(RunLog.seq.asc())
            .all()
        )
        for entry in history:
            await websocket.send_text(entry.line)

        run = db.get(Run, run_id)
        if run is not None and run.status in {"passed", "failed"}:
            await websocket.send_json(
                {"event": "end", "status": run.status, "exit_code": run.exit_code}
            )
            return

        while True:
            message = await queue.get()
            if message == END_SENTINEL:
                fresh = SessionLocal()
                run = fresh.get(Run, run_id)
                status = run.status if run else "failed"
                exit_code = run.exit_code if run else None
                fresh.close()
                await websocket.send_json(
                    {"event": "end", "status": status, "exit_code": exit_code}
                )
                break
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe(run_id, queue)
        db.close()
