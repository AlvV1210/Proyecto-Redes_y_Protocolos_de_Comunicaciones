from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = "core-db"
    postgres_port: int = 5432
    postgres_user: str = "coop_admin"
    postgres_password: str = "core_pass_2026"
    postgres_db: str = "core_bancario"
    postgres_replica_host: str = "replica-db"
    mongo_host: str = "contingencia-db"
    mongo_port: int = 27017
    mongo_db: str = "contingencia_coop"
    prometheus_url: str = "http://monitoreo:9090"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "coop_jwt_secret_academico_2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def replica_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_replica_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
