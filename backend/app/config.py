"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import validator, field_validator
from typing import List
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Boloo"
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:8081"

    # Database
    DATABASE_URL: str = "postgresql://boloo:boloo_dev_password@localhost:5432/boloo"
    DATABASE_SSL_MODE: str = "prefer"  # Options: disable, allow, prefer, require, verify-ca, verify-full

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "boloo-media"
    MINIO_USE_SSL: bool = False

    # Azure Speech Services
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "centralindia"
    AZURE_SUBSCRIPTION_ID: str = ""
    AZURE_RESOURCE_GROUP: str = ""

    # Anthropic (Claude API)
    ANTHROPIC_API_KEY: str = ""

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""  # Fixed: was AZURE_OPENAI_KEY
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o-mini"
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    AZURE_OPENAI_TEMPERATURE: float = 0.3  # Lowered from 0.7 for more consistent, deterministic responses in conversation flow

    # Location Validation Services (optional)
    GOOGLE_MAPS_API_KEY: str = ""  # Optional: Enable Google Maps validation/geocoding if provided
    MAPPLS_API_KEY: str = ""  # Optional: MapMyIndia (5K free/day, best for India)

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    OTP_EMAIL: str = "diptendudip@gmail.com"

    # JWT
    JWT_SECRET_KEY: str = "dev_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # SECURITY: Validate JWT secret in production
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _jwt_secret_secure(cls, v: str, info) -> str:
        """CRITICAL: Prevent default JWT secret in production"""
        # Check if in production mode
        app_env = info.data.get("APP_ENV", "development").lower()

        # Reject default secret in production
        if app_env == "production" and v == "dev_secret_key_change_in_production":
            raise ValueError(
                "SECURITY CRITICAL: Default JWT secret detected in PRODUCTION! "
                "You MUST set a secure JWT_SECRET_KEY environment variable. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # Warn if secret is too short (even in dev)
        if len(v) < 16:
            logger.warning(
                f"⚠️  SECURITY WARNING: JWT_SECRET_KEY is too short ({len(v)} chars). "
                "Minimum 16 characters recommended, 32+ for production."
            )

        return v

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # SLA
    DEFAULT_SLA_HOURS: int = 72

    # Cost Monitoring
    AZURE_COST_ALERT_EMAIL: str = "diptendudip@gmail.com"
    AZURE_COST_LIMIT_USD: float = 20.0
    AZURE_COST_WARNING_THRESHOLD: float = 0.8

    # Push Notifications
    EXPO_ACCESS_TOKEN: str = ""

    # MSG91 SMS Configuration
    MSG91_API_KEY: str = ""
    MSG91_SENDER_ID: str = "BOLOOO"  # 6 chars max, approved by MSG91
    MSG91_TEMPLATE_ID: str = ""  # DLT template ID from MSG91
    MSG91_ROUTE: int = 4  # 4 = Transactional (for OTP)
    MSG91_OTP_EXPIRY_MINUTES: int = 5

    # Pydantic Validators for fail-fast configuration
    @field_validator("AZURE_OPENAI_API_KEY")
    @classmethod
    def _azure_key_present(cls, v: str) -> str:
        """Ensure Azure OpenAI API key is provided"""
        if not v or v.strip() == "":
            raise ValueError("AZURE_OPENAI_API_KEY is required and cannot be empty")
        return v

    @field_validator("AZURE_OPENAI_TEMPERATURE")
    @classmethod
    def _azure_temp_range(cls, v: float) -> float:
        """Ensure temperature is within valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"AZURE_OPENAI_TEMPERATURE must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def _db_url_pg(cls, v: str, info) -> str:
        """Ensure database URL is PostgreSQL with SSL in production"""
        if not (v.startswith("postgres://") or v.startswith("postgresql://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL DSN (postgres:// or postgresql://)")

        # SECURITY FIX #2: Enforce SSL in production
        app_env = info.data.get("APP_ENV", "development").lower()
        ssl_mode = info.data.get("DATABASE_SSL_MODE", "prefer")

        if app_env == "production" and ssl_mode in ["disable", "allow"]:
            raise ValueError(
                "SECURITY CRITICAL: Database SSL must be enabled in production! "
                "Set DATABASE_SSL_MODE to 'require', 'verify-ca', or 'verify-full'"
            )

        # Append SSL parameters if not already present
        if "sslmode=" not in v and app_env == "production":
            separator = "&" if "?" in v else "?"
            v = f"{v}{separator}sslmode={ssl_mode}"
            logger.info(f"Added SSL mode to DATABASE_URL: sslmode={ssl_mode}")

        return v


    @field_validator("AZURE_OPENAI_ENDPOINT")
    @classmethod
    def _azure_endpoint_present(cls, v: str) -> str:
        """Ensure Azure OpenAI endpoint is provided"""
        if not v or v.strip() == "":
            raise ValueError("AZURE_OPENAI_ENDPOINT is required and cannot be empty")
        if not v.startswith("https://"):
            raise ValueError("AZURE_OPENAI_ENDPOINT must start with https://")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.APP_ENV.lower() in ["development", "dev"]


# Global settings instance
settings = Settings()
