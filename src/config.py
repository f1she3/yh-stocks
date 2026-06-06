import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    avg_len: int = int(os.getenv("AVG_LEN", "10"))
    yf_timeout: int = int(os.getenv("YF_TIMEOUT", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cache_ttl: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    cache_dir: str = os.getenv("CACHE_DIR", "/tmp/yh-stocks-cache")
    port: int = int(os.getenv("PORT", "8000"))


def load_config() -> AppConfig:
    return AppConfig()
