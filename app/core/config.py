from pydantic import BaseModel, Field
import os

class Settings(BaseModel):
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    # SIA-DC listener
    SIA_HOST: str = Field(default=os.getenv("SIA_HOST", ""))  # '' binds all interfaces
    SIA_PORT: int = Field(default=int(os.getenv("SIA_PORT", "65100")))
    SIA_ACCOUNTS: list[str] = Field(
        default=[x.strip() for x in os.getenv("SIA_ACCOUNTS", "AAA").split(",") if x.strip()]
    )
    SIA_KEYS: list[str] = Field(
        default=[x.strip() for x in os.getenv("SIA_KEYS", "").split(",")]
    )  # optional; 16/24/32 chars

    # Forwarding target (Frappe)
    FORWARD_URL: str = Field(default=os.getenv("FORWARD_URL", "http://localhost:9000/ingest"))
    FORWARD_AUTH_HEADER: str = Field(default=os.getenv("FORWARD_AUTH_HEADER", ""))
    FORWARD_COOKIE: str = Field(default=os.getenv("FORWARD_COOKIE", ""))  # keep semicolons intact
    FORWARD_TIMEOUT: float = Field(default=float(os.getenv("FORWARD_TIMEOUT", "5")))
    FORWARD_MAX_RETRIES: int = Field(default=int(os.getenv("FORWARD_MAX_RETRIES", "5")))
    FORWARD_RETRY_BASE_DELAY: float = Field(default=float(os.getenv("FORWARD_RETRY_BASE_DELAY", "0.5")))
    FORWARD_EXTRA_HEADERS: dict[str, str] = Field(
        default_factory=lambda: (
            dict(
                (k.strip(), v.strip())
                for k, v in (
                    h.split(":", 1) for h in os.getenv("FORWARD_EXTRA_HEADERS", "").split(";") if ":" in h
                )
            )
            if os.getenv("FORWARD_EXTRA_HEADERS")
            else {}
        )
    )

    # Extras
    APP_TIMEZONE: str = Field(default=os.getenv("APP_TIMEZONE", "Asia/Jakarta"))
    HEARTBEAT_CODES: list[str] = Field(
        default=[x.strip() for x in os.getenv("HEARTBEAT_CODES", "").split(",") if x.strip()]
    )

settings = Settings()
