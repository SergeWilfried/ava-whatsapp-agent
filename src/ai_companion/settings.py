from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    GROQ_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    TOGETHER_API_KEY: str

    QDRANT_API_KEY: str | None
    QDRANT_URL: str
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None

    TEXT_MODEL_NAME: str = "llama-3.3-70b-versatile"
    SMALL_TEXT_MODEL_NAME: str = "llama-3.1-8b-instant"
    STT_MODEL_NAME: str = "whisper-large-v3-turbo"
    TTS_MODEL_NAME: str = "eleven_flash_v2_5"
    TTI_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell-Free"
    ITT_MODEL_NAME: str = "llama-3.2-90b-vision-preview"

    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5

    SHORT_TERM_MEMORY_DB_PATH: str = "/app/data/memory.db"
    LANGUAGE: str = "auto"  # Language: "auto" for automatic detection, or specific code like "en", "fr", "es", "de"

    # Restaurant Configuration
    RESTAURANT_NAME: str = "Tasty Bites Restaurant"
    RESTAURANT_PHONE: str = "(555) 123-4567"
    RESTAURANT_ADDRESS: str = "123 Main Street, Downtown"
    ENABLE_DELIVERY: bool = True
    ENABLE_PICKUP: bool = True
    DELIVERY_FEE: float = 3.50
    FREE_DELIVERY_MINIMUM: float = 25.00
    TAX_RATE: float = 0.08  # 8% tax rate


settings = Settings()
