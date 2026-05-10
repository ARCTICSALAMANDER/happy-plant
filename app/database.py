from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from app.config import settings
from app.models import Base
from contextlib import contextmanager


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    # poolclass=StaticPool,
)

sess_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


def get_session() -> Session:
    return sess_local()


@contextmanager
def get_session_context(): # испольовать везде, где нужно работать с базой данных, чтобы не забывать закрывать сессию и обрабатывать исключения
    db = sess_local()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# # Dependency for FastAPI, у меня фласк поэтому не нужно
# def get_db():
#     db = sess_local()
#     try:
#         yield db
#     finally:
#         db.close()