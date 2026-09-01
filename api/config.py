import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
        self.OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")

    def validate(self) -> None:
        if not self.GROQ_API_KEY and not self.OPENROUTER_API_KEY:
            raise ValueError(
                "[CONFIG ERROR] Debes configurar al menos GROQ_API_KEY o OPENROUTER_API_KEY en tu .env"
            )

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def groq_api_key(self) -> str | None:
        return self.GROQ_API_KEY

    @property
    def openrouter_api_key(self) -> str | None:
        return self.OPENROUTER_API_KEY


config = Config()
config.validate()