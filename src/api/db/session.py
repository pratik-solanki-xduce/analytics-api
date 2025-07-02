import sqlmodel
from sqlmodel import SQLModel, Session, create_engine
import timescaledb

from .config import DATABASE_URL, DB_TIMEZONE

if DATABASE_URL == "":
    raise NotImplementedError("DATABASE_URL needs to be set")

if DATABASE_URL.startswith("sqlite:///"):
    # Use SQLite in local environment
    SQLITE_FILE_PATH = "local.db"
    DATABASE_URL = f"sqlite:///{SQLITE_FILE_PATH}"
    engine = create_engine(DATABASE_URL, echo=True)
    print(f"[INFO] Using local SQLite database at {SQLITE_FILE_PATH}")
else:
    if not timescaledb:
        raise ImportError("TimescaleDB module is required for non-SQLite databases")
    engine = timescaledb.create_engine(DATABASE_URL, timezone=DB_TIMEZONE)
    print(f"[INFO] Using TimescaleDB at {DATABASE_URL}")


def init_db():
    print("Creating tables...")
    # SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite:///"):
        print("SQLite does not support hypertables. Skipping Timescale-specific setup.")
    else:
        print("Creating hypertables...")
        timescaledb.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session