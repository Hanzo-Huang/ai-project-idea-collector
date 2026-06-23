from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    app_name: str = "AI Project Idea Collector"
    environment: str = "development"
    postgres_url: str = "postgresql+asyncpg://collector:collector@localhost:5432/collector"
    qdrant_url: str = "http://localhost:6333"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    classification_model: str = ""
    chat_model: str = ""
    embedding_provider: str = "openai"
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    collector_interval: int = 60
    auto_collection_enabled: bool = True
    classification_prompt: str = "Classify this item for RK3576/RK3588 AI project discovery. Prefer edge AI, NPU deployability, computer vision, audio, robotics, agents, multimodal demos, and major AI events that can inspire Rockchip board content."
    source_filtering_prompt: str = "Keep useful AI projects, demos, model releases, tutorials, hardware deployments, and major AI events that could inspire RK3576/RK3588 content."
    github_token: str = ""
    app_api_key: str = ""
    mcp_api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
