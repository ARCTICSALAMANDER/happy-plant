from sqlalchemy.orm import Session
from app.models import FrequencyEnum, User, Plant, WateringLog, WateringSchedule
import bcrypt
import datetime


def create_user(session: Session, username: str, password: str):
    helper = session.query(User).filter_by(username=username).first()
    if helper:
        return None

    new_user = User(username=username, hashed_password=bcrypt.hashpw(
        password.encode(), bcrypt.gensalt()))
    session.add(new_user)
    session.commit()

    return new_user


def verify_password(session: Session, username: str, password: str):
    user = session.query(User).filter_by(username=username).first()
    return user if bcrypt.checkpw(password.encode(), user.hashed_password) else None


def get_user_by_username(session: Session, username: str):
    return session.query(User).filter_by(username=username).first()


def get_user_by_id(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()


def create_plant(session: Session, user_id: int, name: str, species: str, photo_url: str, description: str, watering_frequency: FrequencyEnum):
    plant = Plant(user_id=user_id, name=name, species=species, description=description, photo_url=photo_url, created_at=datetime.datetime.now(datetime.timezone.utc))
    session.add(plant)
    session.commit()

    plant_id = session.query(Plant).filter_by(name=name, user_id=user_id).first().id
    watering_schedule = WateringSchedule(plant_id=plant_id, frequency=watering_frequency)
    session.add(watering_schedule)
    session.commit()

    return plant


def get_user_plants(session: Session, user_id: int):
    plants = list(session.query(Plant).filter_by(user_id=user_id).all())
    return plants


def get_plant_by_id(session: Session, plant_id: int):
    return session.query(Plant).filter_by(id=plant_id).first()


def delete_plant(session: Session, plant_id: int):
    plant = session.query(Plant).filter_by(id=plant_id).first()
    session.delete(plant)
    session.commit()

    return plant


def update_user_password(session: Session, user_id: int, new_password: str):
    user = session.query(User).filter_by(id=user_id).first()
    user.hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    session.commit()

    return user


def update_user_username(session: Session, user_id: int, new_username: str):
    user = session.query(User).filter_by(id=user_id).first()
    user.username = new_username
    session.commit()

    return user


def create_watering_log(session: Session, plant_id: int, watered_at: datetime.datetime):
    watering_log = WateringLog(plant_id=plant_id, watered_at=watered_at, created_at=datetime.datetime.now(datetime.timezone.utc))
    session.add(watering_log)
    session.commit()

    return watering_log


def get_water_needing_plants(session: Session, user_id: int):
    plants = get_user_plants(session, user_id)
    res = []

    for plant in plants:
        freq_row = session.query(WateringSchedule.frequency).filter_by(plant_id=plant.id).first()
        if not freq_row:
            continue
        
        freq = freq_row[0]

        waterings = session.query(WateringLog.watered_at).filter_by(plant_id=plant.id).order_by(WateringLog.watered_at.desc()).all()
        
        if waterings:
            last_watering = waterings[0][0]

            if freq == FrequencyEnum.EVERY_3_DAYS:
                if datetime.datetime.now() - last_watering >= datetime.timedelta(days=3):
                    res.append(plant)
            elif freq == FrequencyEnum.WEEKLY:
                if datetime.datetime.now() - last_watering >= datetime.timedelta(days=7):
                    res.append(plant)
            elif freq == FrequencyEnum.BIWEEKLY:
                if datetime.datetime.now() - last_watering >= datetime.timedelta(days=14):
                    res.append(plant)
        else:
            if freq != FrequencyEnum.NO_INFO:
                res.append(plant)
        
    return res