"""应用配置 - 从环境变量加载"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # LLM 配置
    llm_api_key: str
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"

    # 高德地图
    amap_api_key: str

    # Unsplash
    unsplash_access_key: str = ""

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
