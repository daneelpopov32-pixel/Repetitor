from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Репетитор"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://repetitor:repetitor@localhost:5432/repetitor"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://repetitor:repetitor@localhost:5432/repetitor"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    GIGACHAT_API_URL: str = "https://api.sbercloud.ru/v1/chat/completions"
    GIGACHAT_API_KEY: str = ""
    GIGACHAT_TIMEOUT: int = 30

    S3_ENDPOINT: str = ""
    S3_BUCKET: str = "repetitor-media"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
