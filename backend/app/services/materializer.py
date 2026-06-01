from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.config import ENGINE_TEMPLATES
from app.models import AIConfig, LLMConfig, Project, Suite

# Mapping of Suite column -> engine layer directory.
LAYER_FIELDS = {
    "cases": "cases_yaml",
    "data": "data_yaml",
    "elements": "elements_yaml",
    "modules": "modules_yaml",
    "vars": "vars_yaml",
    "generation": "generation_yaml",
}


def _default_ai_config_text() -> str:
    path = ENGINE_TEMPLATES / "config" / "ai_config.yaml"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "runtime:\n  default_mode: strict\n  ai_enabled: true\n"


def build_env_config(project: Project) -> dict:
    environments = {
        env.name: (env.base_url or "") for env in project.environments
    }
    return {
        "projects": {
            project.key: {
                "test_dir": f"test_data/{project.key}",
                "environments": environments,
                "browser_config": {
                    "viewport": {
                        "width": project.viewport_width,
                        "height": project.viewport_height,
                    },
                    "tracing": project.tracing or "off",
                },
            }
        }
    }


def build_env_file(llm: LLMConfig | None, base_url: str | None) -> tuple[str, dict]:
    """Returns (.env text, env var dict) for the LLM + base url settings."""
    env_vars: dict[str, str] = {}
    if llm:
        if llm.base_url:
            env_vars["LLM_BASE_URL"] = llm.base_url
        if llm.api_key:
            env_vars["LLM_API_KEY"] = llm.api_key
        if llm.model:
            env_vars["LLM_MODEL"] = llm.model
        if llm.reasoning_effort:
            env_vars["LLM_REASONING_EFFORT"] = llm.reasoning_effort
        if llm.response_format:
            env_vars["LLM_RESPONSE_FORMAT"] = llm.response_format
        if llm.timeout_seconds:
            env_vars["LLM_TIMEOUT_SECONDS"] = str(llm.timeout_seconds)
        if llm.data_policy:
            env_vars["LLM_DATA_POLICY"] = llm.data_policy
    if base_url:
        env_vars["BASE_URL"] = base_url

    lines = [f"{key}={value}" for key, value in env_vars.items()]
    return "\n".join(lines) + ("\n" if lines else ""), env_vars


def materialize_project(db: Session, project: Project, workspace: Path, env: str) -> dict:
    """Write the full engine workspace for a project into `workspace`.

    Returns extra environment variables that should be passed to the subprocess.
    """
    workspace.mkdir(parents=True, exist_ok=True)

    # 1. config/env_config.yaml
    config_dir = workspace / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    env_config = build_env_config(project)
    (config_dir / "env_config.yaml").write_text(
        yaml.safe_dump(env_config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # 2. config/ai_config.yaml
    ai_config: AIConfig | None = project.ai_config
    ai_text = (ai_config.content_yaml if ai_config else "") or _default_ai_config_text()
    (config_dir / "ai_config.yaml").write_text(ai_text, encoding="utf-8")

    # 3. test_data/<key>/<layer>/<suite>.yaml
    test_dir = workspace / "test_data" / project.key
    suites: list[Suite] = list(project.suites)
    for suite in suites:
        for layer, field in LAYER_FIELDS.items():
            content = (getattr(suite, field) or "").strip()
            if not content:
                continue
            layer_dir = test_dir / layer
            layer_dir.mkdir(parents=True, exist_ok=True)
            (layer_dir / f"{suite.name}.yaml").write_text(
                getattr(suite, field), encoding="utf-8"
            )

    # 4. .env (LLM settings + selected env base url)
    base_url = ""
    for environment in project.environments:
        if environment.name == env:
            base_url = environment.base_url
            break
    env_text, env_vars = build_env_file(project.llm_config, base_url)
    (workspace / ".env").write_text(env_text, encoding="utf-8")

    return env_vars
