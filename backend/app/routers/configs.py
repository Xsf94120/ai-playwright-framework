from __future__ import annotations

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import AIConfig, LLMConfig, Project
from app.schemas import (
    AIConfigIn,
    AIConfigOut,
    LLMConfigIn,
    LLMConfigOut,
)
from app.services.materializer import default_ai_config_text

router = APIRouter(
    prefix="/projects/{project_id}",
    tags=["configs"],
    dependencies=[Depends(get_current_user)],
)


def _project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


# ---- LLM configuration ----
@router.get("/llm", response_model=LLMConfigOut)
def get_llm(project_id: int, db: Session = Depends(get_db)) -> LLMConfigOut:
    project = _project_or_404(db, project_id)
    llm = project.llm_config or LLMConfig(project_id=project.id)
    out = LLMConfigOut.model_validate(llm)
    # Never expose the stored key; only signal whether it is set.
    out.api_key = ""
    out.api_key_set = bool(llm.api_key)
    return out


@router.put("/llm", response_model=LLMConfigOut)
def update_llm(
    project_id: int, payload: LLMConfigIn, db: Session = Depends(get_db)
) -> LLMConfigOut:
    project = _project_or_404(db, project_id)
    llm = project.llm_config
    if llm is None:
        llm = LLMConfig(project_id=project.id)
        db.add(llm)
    llm.base_url = payload.base_url
    # Keep the existing key when the client submits a blank value (masked field).
    if payload.api_key:
        llm.api_key = payload.api_key
    llm.model = payload.model
    llm.reasoning_effort = payload.reasoning_effort
    llm.response_format = payload.response_format
    llm.timeout_seconds = payload.timeout_seconds
    llm.data_policy = payload.data_policy
    db.commit()
    db.refresh(llm)
    out = LLMConfigOut.model_validate(llm)
    out.api_key = ""
    out.api_key_set = bool(llm.api_key)
    return out


# ---- AI runtime configuration (raw YAML) ----
@router.get("/ai-config", response_model=AIConfigOut)
def get_ai_config(project_id: int, db: Session = Depends(get_db)) -> AIConfigOut:
    project = _project_or_404(db, project_id)
    ai = project.ai_config
    content = (ai.content_yaml if ai else "") or default_ai_config_text()
    return AIConfigOut(content_yaml=content)


@router.put("/ai-config", response_model=AIConfigOut)
def update_ai_config(
    project_id: int, payload: AIConfigIn, db: Session = Depends(get_db)
) -> AIConfigOut:
    project = _project_or_404(db, project_id)
    try:
        yaml.safe_load(payload.content_yaml)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=400, detail=f"YAML 格式错误: {exc}") from exc
    ai = project.ai_config
    if ai is None:
        ai = AIConfig(project_id=project.id)
        db.add(ai)
    ai.content_yaml = payload.content_yaml
    db.commit()
    return AIConfigOut(content_yaml=ai.content_yaml)
