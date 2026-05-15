from sqlalchemy.orm import Session
from models import User, Plant
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


def verify_password(session: Session, username: str, password: str):
    user = session.query(User).filter_by(username=username)
    return bcrypt.checkpw(password.encode(), User["hashed_password"])


def get_user_by_username():
    pass


def get_user_by_id(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()


def create_plant(session: Session, user_id: int, name: str, photo_url: str, watering_frequency: str, watering_time: str, watering_amount: int):
    desc = f"water it {watering_frequency} with {watering_amount} ml of water"
    plant = Plant(user_id=user_id, name=name, description=desc, photo_url=photo_url, created_at=datetime.datetime.now(datetime.timezone.utc))
    session.add(plant)
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


def update_user_password(session: Session, user_id: int, new_password: str):
    user = session.query(User).filter_by(id=user_id).first()
    user.hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
