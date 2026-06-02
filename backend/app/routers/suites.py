from __future__ import annotations

import re

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Project, Suite
from app.schemas import SuiteCreate, SuiteOut, SuiteSummary, SuiteUpdate

router = APIRouter(
    prefix="/projects/{project_id}/suites",
    tags=["suites"],
    dependencies=[Depends(get_current_user)],
)

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_LAYER_FIELDS = [
    "cases_yaml",
    "data_yaml",
    "elements_yaml",
    "modules_yaml",
    "vars_yaml",
    "generation_yaml",
]


def _project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _suite_or_404(db: Session, project_id: int, suite_id: int) -> Suite:
    suite = db.get(Suite, suite_id)
    if suite is None or suite.project_id != project_id:
        raise HTTPException(status_code=404, detail="用例集不存在")
    return suite


def _validate_yaml(label: str, content: str | None) -> None:
    if not content or not content.strip():
        return
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(
            status_code=400, detail=f"{label} YAML 格式错误: {exc}"
        ) from exc


@router.get("", response_model=list[SuiteSummary])
def list_suites(project_id: int, db: Session = Depends(get_db)) -> list[Suite]:
    _project_or_404(db, project_id)
    return (
        db.query(Suite)
        .filter(Suite.project_id == project_id)
        .order_by(Suite.updated_at.desc())
        .all()
    )


@router.post("", response_model=SuiteOut, status_code=201)
def create_suite(
    project_id: int, payload: SuiteCreate, db: Session = Depends(get_db)
) -> Suite:
    _project_or_404(db, project_id)
    name = payload.name.strip()
    if not NAME_RE.match(name):
        raise HTTPException(
            status_code=400, detail="用例集名称只能包含字母、数字和下划线，且以字母开头"
        )
    if (
        db.query(Suite)
        .filter(Suite.project_id == project_id, Suite.name == name)
        .first()
    ):
        raise HTTPException(status_code=400, detail="同名用例集已存在")

    for field in _LAYER_FIELDS:
        _validate_yaml(field, getattr(payload, field))

    suite = Suite(
        project_id=project_id,
        name=name,
        description=payload.description,
        cases_yaml=payload.cases_yaml,
        data_yaml=payload.data_yaml,
        elements_yaml=payload.elements_yaml,
        modules_yaml=payload.modules_yaml,
        vars_yaml=payload.vars_yaml,
        generation_yaml=payload.generation_yaml,
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return suite


@router.get("/{suite_id}", response_model=SuiteOut)
def get_suite(
    project_id: int, suite_id: int, db: Session = Depends(get_db)
) -> Suite:
    return _suite_or_404(db, project_id, suite_id)


@router.put("/{suite_id}", response_model=SuiteOut)
def update_suite(
    project_id: int,
    suite_id: int,
    payload: SuiteUpdate,
    db: Session = Depends(get_db),
) -> Suite:
    suite = _suite_or_404(db, project_id, suite_id)
    data = payload.model_dump(exclude_unset=True)
    for field in _LAYER_FIELDS:
        if field in data:
            _validate_yaml(field, data[field])
    for key, value in data.items():
        setattr(suite, key, value)
    db.commit()
    db.refresh(suite)
    return suite


@router.delete("/{suite_id}", status_code=204)
def delete_suite(
    project_id: int, suite_id: int, db: Session = Depends(get_db)
) -> None:
    suite = _suite_or_404(db, project_id, suite_id)
    db.delete(suite)
    db.commit()
