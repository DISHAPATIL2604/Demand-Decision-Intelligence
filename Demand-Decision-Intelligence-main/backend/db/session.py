from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Create all ORM-mapped tables that do not yet exist in the database.

    Called once at application startup (see main.py lifespan hook).
    This is appropriate for development and initial deployment.
    For production migrations use Alembic instead.
    """
    # Import models here to ensure they are registered with Base.metadata
    # before create_all is called.
    import backend.db.models  # noqa: F401  (side-effect import)
    Base.metadata.create_all(bind=engine, checkfirst=True)
