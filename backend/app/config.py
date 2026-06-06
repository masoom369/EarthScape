from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "earthscape"
    jwt_secret: str
    jwt_expire_minutes: int = 60
    hdfs_namenode_host: str = "localhost"
    hdfs_webhdfs_port: int = 9870
    yarn_rm_port: int = 8088
    hadoop_streaming_jar: str = (
        "/usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar"
    )
    cors_origins: str = "http://localhost:5173"
    alert_cache_ttl_seconds: int = 60
    realtime_producer_interval: int = 10
    default_admin_email: str = "admin@earthscape.com"
    default_admin_password: str = "Admin123!"
    archive_threshold_days: int = 365
    mapreduce_default_fill: float = -9999.0

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def webhdfs_base_url(self) -> str:
        return f"http://{self.hdfs_namenode_host}:{self.hdfs_webhdfs_port}/webhdfs/v1"

    @property
    def yarn_base_url(self) -> str:
        return f"http://{self.hdfs_namenode_host}:{self.yarn_rm_port}/ws/v1/cluster"


@lru_cache
def get_settings() -> Settings:
    return Settings()