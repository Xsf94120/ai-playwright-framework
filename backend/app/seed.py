from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import ENGINE_TEMPLATES
from app.models import AIConfig, Environment, LLMConfig, Project, Suite, User
from app.security import hash_password

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

ENV_NAMES = ["dev", "test", "stage", "prod"]


def _read_template(*parts: str) -> str:
    path = ENGINE_TEMPLATES.joinpath(*parts)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _default_ai_config_yaml() -> str:
    content = _read_template("config", "ai_config.yaml")
    return content or "runtime:\n  default_mode: strict\n  ai_enabled: true\n"


def seed_initial_data(db: Session) -> None:
    _seed_admin(db)
    _seed_demo_project(db)
    db.commit()


def _seed_admin(db: Session) -> None:
    if db.query(User).filter(User.username == DEFAULT_ADMIN_USER).first():
        return
    db.add(
        User(
            username=DEFAULT_ADMIN_USER,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        )
    )


def _seed_demo_project(db: Session) -> None:
    if db.query(Project).filter(Project.key == "demo").first():
        return

    project = Project(
        key="demo",
        name="Demo 示例项目",
        description="基于 SauceDemo 的内置示例项目，演示登录、加购物车与退出流程。",
        viewport_width=1280,
        viewport_height=720,
        tracing="off",
    )
    db.add(project)
    db.flush()

    for name in ENV_NAMES:
        db.add(
            Environment(
                project_id=project.id,
                name=name,
                base_url="https://www.saucedemo.com/",
            )
        )

    db.add(LLMConfig(project_id=project.id))
    db.add(AIConfig(project_id=project.id, content_yaml=_default_ai_config_yaml()))

    db.add(
        Suite(
            project_id=project.id,
            name="saucedemo_ai",
            description="SauceDemo 标准用户完整购物车流程",
            cases_yaml=_read_template(
                "test_data", "demo", "cases", "saucedemo_ai.yaml"
            ),
            elements_yaml=_read_template(
                "test_data", "demo", "elements", "saucedemo_ai.yaml"
            ),
            generation_yaml=_read_template(
                "test_data", "demo", "generation", "saucedemo_ai.yaml"
            ),
            data_yaml=_read_template(
                "test_data", "demo", "data", "saucedemo_ai.yaml"
            ),
            modules_yaml=_read_template(
                "test_data", "demo", "modules", "saucedemo_ai.yaml"
            ),
            vars_yaml=_read_template(
                "test_data", "demo", "vars", "saucedemo_ai.yaml"
            ),
        )
    )
