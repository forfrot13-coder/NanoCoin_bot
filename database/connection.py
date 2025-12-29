from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base
from database.admin_models import Base as AdminBase
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Create all tables from models
    Base.metadata.create_all(bind=engine)
    # Create all tables from admin_models
    AdminBase.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
