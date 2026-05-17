from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    
    PLANT_CARE_API_KEY: str
    PLANT_CARE_URL: str

    PLANT_ID_URL: str
    PLANT_ID_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()