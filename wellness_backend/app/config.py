from pydantic_settings import BaseSettings


# Configuration class that loads application settings from environment variables.
class Settings(BaseSettings):
    groq_api_key: str  # API key required to access Groq LLM services

    class Config:
        env_file = ".env"  # Automatically load variables from a .env file


# Instantiate settings so they can be imported and used across the project.
settings = Settings()
