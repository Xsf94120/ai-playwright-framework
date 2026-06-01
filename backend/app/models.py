from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    viewport_width: Mapped[int] = mapped_column(Integer, default=1280)
    viewport_height: Mapped[int] = mapped_column(Integer, default=720)
    tracing: Mapped[str] = mapped_column(String(16), default="off")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    environments: Mapped[list["Environment"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    suites: Mapped[list["Suite"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    llm_config: Mapped["LLMConfig"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    ai_config: Mapped["AIConfig"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )


class Environment(Base):
    __tablename__ = "environments"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_env_project"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(16), nullable=False)  # dev/test/stage/prod
    base_url: Mapped[str] = mapped_column(String(512), default="")

    project: Mapped[Project] = relationship(back_populates="environments")


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    base_url: Mapped[str] = mapped_column(String(512), default="")
    api_key: Mapped[str] = mapped_column(String(512), default="")
    model: Mapped[str] = mapped_column(String(128), default="")
    reasoning_effort: Mapped[str] = mapped_column(String(32), default="medium")
    response_format: Mapped[str] = mapped_column(String(32), default="auto")
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    data_policy: Mapped[str] = mapped_column(String(32), default="external")

    project: Mapped[Project] = relationship(back_populates="llm_config")


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    content_yaml: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[Project] = relationship(back_populates="ai_config")


class Suite(Base):
    """A logical test suite mapping to the engine's layered YAML files
    (cases / data / elements / modules / vars / generation) sharing a base name."""

    __tablename__ = "suites"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_suite_project"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    cases_yaml: Mapped[str] = mapped_column(Text, default="")
    data_yaml: Mapped[str] = mapped_column(Text, default="")
    elements_yaml: Mapped[str] = mapped_column(Text, default="")
    modules_yaml: Mapped[str] = mapped_column(Text, default="")
    vars_yaml: Mapped[str] = mapped_column(Text, default="")
    generation_yaml: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="suites")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    project_key: Mapped[str] = mapped_column(String(64), default="")
    suite_name: Mapped[str] = mapped_column(String(128), default="")
    kind: Mapped[str] = mapped_column(String(16), default="run")  # run / generate
    status: Mapped[str] = mapped_column(String(16), default="pending")
    ai_mode: Mapped[str] = mapped_column(String(16), default="strict")
    env: Mapped[str] = mapped_column(String(16), default="prod")
    browser: Mapped[str] = mapped_column(String(16), default="chromium")
    headed: Mapped[bool] = mapped_column(Boolean, default=False)
    command: Mapped[str] = mapped_column(Text, default="")
    exit_code: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    logs: Mapped[list["RunLog"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RunLog(Base):
    __tablename__ = "run_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer, default=0)
    line: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped[Run] = relationship(back_populates="logs")
