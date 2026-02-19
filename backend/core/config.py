"""Application configuration loaded from environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # NebulaGraph
    nebula_graphd_host: str = "127.0.0.1"
    nebula_graphd_port: int = 9669
    nebula_user: str = "root"
    nebula_password: str = "nebula"
    nebula_space: str = "graphops"

    # Qdrant
    qdrant_host: str = "127.0.0.1"
    qdrant_port: int = 9333

    # Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 9379

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 9200

    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"

    # Paths (relative to project root)
    schemas_dir: str = "schemas"
    specs_dir: str = "specs"
    rules_dir: str = "rules"
    aliases_dir: str = "aliases"

    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent

    model_config = {"env_file": ".env", "env_prefix": "", "extra": "ignore"}


settings = Settings()
