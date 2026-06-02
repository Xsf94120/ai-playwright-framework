from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import AIConfig, Environment, LLMConfig, Project
from app.schemas import EnvironmentIn, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.materializer import default_ai_config_text

router = APIRouter(
    prefix="/projects", tags=["projects"], dependencies=[Depends(get_current_user)]
)

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    key = payload.key.strip().lower()
    if not KEY_RE.match(key):
        raise HTTPException(
            status_code=400, detail="项目标识只能包含小写字母、数字和下划线，且以字母开头"
        )
    if db.query(Project).filter(Project.key == key).first():
        raise HTTPException(status_code=400, detail="项目标识已存在")

    project = Project(
        key=key,
        name=payload.name,
        description=payload.description,
        viewport_width=payload.viewport_width,
        viewport_height=payload.viewport_height,
        tracing=payload.tracing,
    )
    db.add(project)
    db.flush()

    # 至少保证一个环境，避免项目建好后无法运行。
    envs = payload.environments or [
        EnvironmentIn(name="prod", base_url="")
    ]
    for env in envs:
        db.add(
            Environment(project_id=project.id, name=env.name, base_url=env.base_url)
        )

    db.add(LLMConfig(project_id=project.id))
    db.add(AIConfig(project_id=project.id, content_yaml=default_ai_config_text()))
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    return _get_project_or_404(db, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)
) -> Project:
    project = _get_project_or_404(db, project_id)
    project.name = payload.name
    project.description = payload.description
    project.viewport_width = payload.viewport_width
    project.viewport_height = payload.viewport_height
    project.tracing = payload.tracing

    # Replace environments wholesale.
    existing = {e.name: e for e in project.environments}
    incoming_names = {e.name for e in payload.environments}
    for env in payload.environments:
        if env.name in existing:
            existing[env.name].base_url = env.base_url
        else:
            db.add(
                Environment(
                    project_id=project.id, name=env.name, base_url=env.base_url
                )
            )
    for name, env in existing.items():
        if name not in incoming_names:
            db.delete(env)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    project = _get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
