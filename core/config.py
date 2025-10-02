"""Application configuration and feature flags.

Provide a minimal `settings` object so other modules can import
`from core.config import settings`.
"""
from dataclasses import dataclass
import os


@dataclass
class Settings:
	ENV: str = os.getenv("APP_ENV", os.getenv("ENV", "development"))
	DEBUG: bool = os.getenv("DEBUG", "0") in ("1", "true", "True")


settings = Settings()
