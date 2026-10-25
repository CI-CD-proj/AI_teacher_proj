from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Mektep AI"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 12
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./data/app.db"
    upload_dir: str = "./data/uploads"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


settings = Settings()

if settings.database_url.startswith("sqlite:///./"):
    db_path = BACKEND_DIR / settings.database_url.replace("sqlite:///./", "")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.database_url = f"sqlite:///{db_path}"

upload = Path(settings.upload_dir)
if not upload.is_absolute():
    settings.upload_dir = str((BACKEND_DIR / upload).resolve())

