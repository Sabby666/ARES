# backend/app/core/config.py
"""Application configuration using pydantic-settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# Resolve data directory relative to the backend folder
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _BACKEND_DIR.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DATA_DIR / "ares.db"


class Settings(BaseSettings):
    APP_NAME: str = "ARES Security Prototype"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    APP_ENV: str = "development"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_DB_PATH}")

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # LLM
    LLM_PROVIDER: str = "mock"  # 'mock' or 'omniroute'
    LLM_BASE_URL: str = "http://localhost:20128/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 120

    # Tool Execution
    TOOL_PROVIDER: str = "mock"  # 'mock' or 'hexstrike'
    TOOL_TIMEOUT_SECONDS: int = 30
    HEXSTRIKE_BASE_URL: str = "http://127.0.0.1:8888/api/v1"
    HEXSTRIKE_API_KEY: str = ""


    # Policy – allowed targets
    ALLOWED_TARGETS: List[str] = [
        "localhost",
        "127.0.0.1",
        "demo.local",
        "http://localhost",
        "http://127.0.0.1",
        "http://demo.local",
        "https://localhost",
        "https://127.0.0.1",
        "https://demo.local",
    ]

    # Agent delays (ms) for demo visualization
    DELAY_POLICY_MS: int = 500
    DELAY_RECON_MS: int = 1200
    DELAY_ANALYSIS_MS: int = 1200
    DELAY_LLM_MS: int = 1200
    DELAY_VALIDATION_MS: int = 1000
    DELAY_EVIDENCE_MS: int = 700
    DELAY_REPORT_MS: int = 800

    # VAPT Loop configuration
    MAX_VAPT_ACTIONS: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
