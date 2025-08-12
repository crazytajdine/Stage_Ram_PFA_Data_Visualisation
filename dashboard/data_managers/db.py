# db.py
import os, logging
from sqlalchemy import create_engine

def get_engine():
    url = os.getenv("DATABASE_URL")

    engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800, future=True)
    return engine
