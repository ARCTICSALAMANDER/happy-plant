from pydantic import BaseModel, ConfigDict, SecretStr
from datetime import datetime
from app.models import FrequencyEnum


class UserCreate(BaseModel):
    username: str
    password: SecretStr

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    new_username: str | None = None
    new_password: SecretStr | None = None

    model_config = ConfigDict(extra="forbid")


class PlantCreate(BaseModel):
    name: str
    description: str | None = None
    photo_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class PlantInfo(BaseModel): # ответ от определителя растений подогнать под этот шаблон
    name: str
    description: str | None = None
    watering_frequency: FrequencyEnum | None = None