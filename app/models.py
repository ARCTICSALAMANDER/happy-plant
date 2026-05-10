from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, Enum
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import enum


# функционал подразумевает подсказать пользователю только когда и сколько полить растение,
# подробности по тому, куда ставить, какую землю использовать и т.д. можно оставить в описании


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    plants = relationship("Plant", back_populates="owner", cascade="all, delete-orphan")


class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    photo_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="plants")
    watering_schedules = relationship("WateringSchedule", back_populates="plant", cascade="all, delete-orphan")
    watering_logs = relationship("WateringLog", back_populates="plant", cascade="all, delete-orphan")


class FrequencyEnum(str, enum.Enum):
    DAILY = "daily"
    EVERY_2_DAYS = "every_2_days"
    EVERY_3_DAYS = "every_3_days"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly" # раз в 2 недели
    MONTHLY = "monthly"


class WateringSchedule(Base):
    __tablename__ = "watering_schedules"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    frequency = Column(Enum(FrequencyEnum), default=FrequencyEnum.WEEKLY, nullable=False)
    watering_time = Column(String(5), nullable=False)  # время в формате "HH:MM", например "08:00"
    amount_ml = Column(Float, default=500)  # сколько полить в мл
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    plant = relationship("Plant", back_populates="watering_schedules")


class WateringLog(Base):
    __tablename__ = "watering_logs"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    watered_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    
    plant = relationship("Plant", back_populates="watering_logs")