from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth ----
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserOut(ORMModel):
    id: int
    username: str


# ---- Environments ----
class EnvironmentIn(BaseModel):
    name: str
    base_url: str = ""


class EnvironmentOut(ORMModel):
    id: int
    name: str
    base_url: str


# ---- Projects ----
class ProjectBase(BaseModel):
    name: str
    description: str = ""
    viewport_width: int = 1280
    viewport_height: int = 720
    tracing: str = "off"


class ProjectCreate(ProjectBase):
    key: str
    environments: list[EnvironmentIn] = Field(default_factory=list)


class ProjectUpdate(ProjectBase):
    environments: list[EnvironmentIn] = Field(default_factory=list)


class ProjectOut(ORMModel):
    id: int
    key: str
    name: str
    description: str
    viewport_width: int
    viewport_height: int
    tracing: str
    environments: list[EnvironmentOut] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---- LLM config ----
class LLMConfigIn(BaseModel):
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    reasoning_effort: str = "medium"
    response_format: str = "auto"
    timeout_seconds: int = 60
    data_policy: str = "external"


class LLMConfigOut(LLMConfigIn):
    model_config = ConfigDict(from_attributes=True)
    api_key_set: bool = False


# ---- AI config (raw yaml) ----
class AIConfigIn(BaseModel):
    content_yaml: str


class AIConfigOut(BaseModel):
    content_yaml: str


# ---- Suites ----
class SuiteBase(BaseModel):
    name: str
    description: str = ""
    cases_yaml: str = ""
    data_yaml: str = ""
    elements_yaml: str = ""
    modules_yaml: str = ""
    vars_yaml: str = ""
    generation_yaml: str = ""


class SuiteCreate(SuiteBase):
    pass


class SuiteUpdate(BaseModel):
    description: Optional[str] = None
    cases_yaml: Optional[str] = None
    data_yaml: Optional[str] = None
    elements_yaml: Optional[str] = None
    modules_yaml: Optional[str] = None
    vars_yaml: Optional[str] = None
    generation_yaml: Optional[str] = None


class SuiteOut(ORMModel):
    id: int
    project_id: int
    name: str
    description: str
    cases_yaml: str
    data_yaml: str
    elements_yaml: str
    modules_yaml: str
    vars_yaml: str
    generation_yaml: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SuiteSummary(ORMModel):
    id: int
    project_id: int
    name: str
    description: str
    updated_at: Optional[datetime] = None


# ---- Runs ----
class RunCreate(BaseModel):
    project_id: int
    suite_name: str = ""
    ai_mode: str = "strict"
    env: str = "prod"
    browser: str = "chromium"
    headed: bool = False


class GenerateCreate(BaseModel):
    project_id: int
    suite_name: str
    env: str = "prod"
    headed: bool = False


class RunOut(ORMModel):
    id: int
    project_id: int
    project_key: str
    suite_name: str
    kind: str
    status: str
    ai_mode: str
    env: str
    browser: str
    headed: bool
    command: str
    exit_code: Optional[int] = None
    duration: Optional[float] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class RunLogOut(ORMModel):
    seq: int
    line: str
