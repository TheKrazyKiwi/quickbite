import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env from project root or backend root
project_root = Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")
load_dotenv()


class Settings:
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://quickbite:quickbite@localhost:5432/quickbite")
    secret_key = os.getenv("SECRET_KEY", "quickbite-secure-college-demo-secret-key-2026")
    token_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
