from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: int
    username: str
    password: str


class Plant(Base):
    __tablename__ = "plants"

    id: int
    name: str
    description: str
    photo_url: str


class WateringSchedule(Base):
    __tablename__ = "watering_schedules"

    id: int
    plant_id: int
    watering_time: str