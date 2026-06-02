from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.config import ENGINE_ROOT, PYTHON_BIN, RUNS_DIR
from app.db import SessionLocal
from app.models import Project, Run, RunLog, Suite
from app.services.materializer import LAYER_FIELDS, materialize_project

# run_id -> set of subscriber queues for live log streaming
_subscribers: dict[int, set[asyncio.Queue]] = defaultdict(set)
END_SENTINEL = "__RUN_END__"


def subscribe(run_id: int) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[run_id].add(queue)
    return queue


def unsubscribe(run_id: int, queue: asyncio.Queue) -> None:
    _subscribers[run_id].discard(queue)
    if not _subscribers[run_id]:
        _subscribers.pop(run_id, None)


def _publish(run_id: int, message: str) -> None:
    for queue in list(_subscribers.get(run_id, set())):
        queue.put_nowait(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _build_command(run: Run, suite_name: str) -> list[str]:
    if run.kind == "generate":
        cmd = [
            PYTHON_BIN,
            "-m",
            "ai_playwright.cli.generate_case",
            suite_name,
            "-p",
            run.project_key,
            "--headless",
        ]
        return cmd

    cmd = [
        PYTHON_BIN,
        "-m",
        "ai_playwright.cli.run_case",
        "-p",
        run.project_key,
        "-e",
        run.env,
        "--ai-mode",
        run.ai_mode,
        "--browser",
        run.browser,
        "--headed" if run.headed else "--headless",
    ]
    if suite_name:
        cmd.extend(["-f", suite_name])
    return cmd


def _reimport_generated_suites(db, project: Project, workspace: Path) -> None:
    """After generation, sync generated YAML files on disk back into the DB."""
    test_dir = workspace / "test_data" / project.key
    if not test_dir.exists():
        return
    existing = {s.name: s for s in project.suites}
    discovered: dict[str, dict[str, str]] = {}
    for layer, field in LAYER_FIELDS.items():
        layer_dir = test_dir / layer
        if not layer_dir.exists():
            continue
        for file in layer_dir.glob("*.yaml"):
            name = file.stem
            discovered.setdefault(name, {})[field] = file.read_text(encoding="utf-8")
    for name, fields in discovered.items():
        suite = existing.get(name)
        if suite is None:
            suite = Suite(project_id=project.id, name=name, description="AI 生成")
            db.add(suite)
        for field, content in fields.items():
            setattr(suite, field, content)
    db.commit()


async def execute_run(run_id: int) -> None:
    """Background coroutine: materialize workspace, run the engine, stream logs."""
    db = SessionLocal()
    seq = 0

    def log(line: str) -> None:
        nonlocal seq
        seq += 1
        db.add(RunLog(run_id=run_id, seq=seq, line=line))
        db.commit()
        _publish(run_id, line)

    try:
        run = db.get(Run, run_id)
        if run is None:
            return
        project = db.get(Project, run.project_id)
        if project is None:
            run.status = "failed"
            run.finished_at = _now()
            db.commit()
            _publish(run_id, "项目不存在")
            _publish(run_id, END_SENTINEL)
            return

        run.status = "running"
        run.started_at = _now()
        db.commit()

        workspace = RUNS_DIR / f"run_{run_id}"
        log(f"[平台] 准备运行工作区: {workspace}")
        env_vars = materialize_project(db, project, workspace, run.env)
        log("[平台] 已物化配置: config/env_config.yaml, config/ai_config.yaml, test_data, .env")

        suite_name = run.suite_name or ""
        cmd = _build_command(run, suite_name)
        run.command = " ".join(cmd)
        db.commit()
        log(f"[平台] 执行命令: {run.command}")

        sub_env = os.environ.copy()
        sub_env.update(env_vars)
        existing_pythonpath = sub_env.get("PYTHONPATH", "")
        sub_env["PYTHONPATH"] = (
            f"{ENGINE_ROOT}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(ENGINE_ROOT)
        )
        sub_env["PYTHONUNBUFFERED"] = "1"
        sub_env["PYTHONIOENCODING"] = "utf-8"

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(workspace),
            env=sub_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        assert process.stdout is not None
        while True:
            raw = await process.stdout.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            log(line)

        exit_code = await process.wait()
        run.exit_code = exit_code
        run.status = "passed" if exit_code == 0 else "failed"
        run.finished_at = _now()
        db.commit()
        log(f"[平台] 进程结束, 退出码={exit_code}, 状态={run.status}")

        if run.kind == "generate" and exit_code == 0:
            try:
                db.refresh(project)
                _reimport_generated_suites(db, project, workspace)
                log("[平台] 已将生成的用例同步回数据库")
            except Exception as exc:  # noqa: BLE001
                log(f"[平台] 生成结果回写失败: {exc}")
    except Exception as exc:  # noqa: BLE001
        try:
            run = db.get(Run, run_id)
            if run is not None:
                run.status = "failed"
                run.finished_at = _now()
                db.commit()
        except Exception:  # noqa: BLE001
            pass
        log(f"[平台] 运行异常: {exc}")
    finally:
        _publish(run_id, END_SENTINEL)
        db.close()
