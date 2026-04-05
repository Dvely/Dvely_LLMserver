import os
from functools import lru_cache
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.ollama_timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "300"))
        self.ollama_keep_alive: str = os.getenv("OLLAMA_KEEP_ALIVE", "15m")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        api_keys_raw = os.getenv("API_KEYS", "sk-local-dev")
        self.api_keys: List[str] = [k.strip() for k in api_keys_raw.split(",") if k.strip()]

        qwen_alias = os.getenv("MODEL_QWEN_ALIAS", "qwen2.5-coder:3b")
        qwen_name = os.getenv("MODEL_QWEN_NAME", "qwen2.5-coder:3b")
        exaone_alias = os.getenv("MODEL_EXAONE_ALIAS", "exaone-deep:2.4b")
        exaone_name = os.getenv("MODEL_EXAONE_NAME", "exaone-deep:2.4b")

        self.model_alias_map: Dict[str, str] = {
            qwen_alias: qwen_name,
            exaone_alias: exaone_name,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
