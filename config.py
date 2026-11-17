"""Environment-driven configuration for the downloader."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

PORTAL_URL = "https://alectrautilitiesgbportal.savagedata.com"
PORTAL_HOST = "alectrautilitiesgbportal.savagedata.com"
DEFAULT_MODEL = "openai/gpt-oss-20b"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    account_name: str
    account_number: str
    account_phone: str
    db_path: str = "./usage_data.db"
    openrouter_api_key: str = ""
    model: str = DEFAULT_MODEL
    openrouter_base_url: str = OPENROUTER_BASE_URL
    alert_webhook_url: str = ""
    artifacts_dir: str = "./artifacts"
    browser_user_data_dir: str = ""
    headless: bool = True
    llm_enabled: bool = True
    agent_max_steps: int = 12
    agent_timeout_s: int = 300
    agent_use_vision: bool = False
    agent_judge_enabled: bool = True
    cycle_interval_s: int = 4 * 60 * 60

    @property
    def portal_url(self) -> str:
        return PORTAL_URL

    @property
    def portal_host(self) -> str:
        return PORTAL_HOST

    def validate(self) -> None:
        required = {
            "ALECTRA_ACCOUNT_NAME": self.account_name,
            "ALECTRA_ACCOUNT_NUMBER": self.account_number,
            "ALECTRA_ACCOUNT_PHONE": self.account_phone,
        }
        missing = [name for name, value in required.items() if not value]
        if self.llm_enabled and not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def load_settings() -> Settings:
    """Read settings from the environment (and a local .env file)."""
    load_dotenv()
    return Settings(
        account_name=os.getenv("ALECTRA_ACCOUNT_NAME", ""),
        account_number=os.getenv("ALECTRA_ACCOUNT_NUMBER", ""),
        account_phone=os.getenv("ALECTRA_ACCOUNT_PHONE", ""),
        db_path=os.getenv("USAGE_DB_PATH", "./usage_data.db"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
        alert_webhook_url=os.getenv("ALERT_WEBHOOK_URL", ""),
        artifacts_dir=os.getenv("ARTIFACTS_DIR", "./artifacts"),
        browser_user_data_dir=os.getenv("BROWSER_USER_DATA_DIR", ""),
        headless=_env_bool("BROWSER_HEADLESS", True),
        llm_enabled=_env_bool("LLM_FALLBACK_ENABLED", True),
        agent_max_steps=_env_int("AGENT_MAX_STEPS", 12),
        agent_timeout_s=_env_int("AGENT_TIMEOUT_S", 300),
        agent_use_vision=_env_bool("AGENT_USE_VISION", False),
        agent_judge_enabled=_env_bool("AGENT_JUDGE_ENABLED", True),
        cycle_interval_s=_env_int("CYCLE_INTERVAL_S", 4 * 60 * 60),
    )
