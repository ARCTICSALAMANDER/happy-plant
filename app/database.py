from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config import settings


engine = create_engine(settings.DATABASE_URL)


def get_session():
    Session = sessionmaker(bind=engine)
    return Session()