from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # System settings
    app_mode: str = "demo"
    environment: str = "development"
    
    # FortyGuard Settings
    fortyguard_api_key: str = ""
    fortyguard_base_url: str = "https://api.fortyguard.io/v1"
    fortyguard_timeout: float = 10.0
    fortyguard_max_retries: int = 3
    
    # JWT Auth Settings
    jwt_secret_key: str = ""
    jwt_expire_minutes: int = 1440
    
    # Existing settings can also go here, but focusing on FortyGuard as requested
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
