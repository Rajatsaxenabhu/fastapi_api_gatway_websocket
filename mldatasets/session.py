from conf.settings import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if settings.DEBUG:
    if settings.ENV == "local":
        DB_URI = settings.SQLALCHEMY_DATABASE_URL_LOCAL
    else:
        DB_URI = settings.SQLALCHEMY_DATABASE_URL_DEV
else:
    DB_URI = settings.SQLALCHEMY_DATABASE_URL_PROD

engine = create_engine(
    DB_URI,
    pool_pre_ping=True,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_POOL,
    echo=settings.POSTGRES_ENGINE_ECHO
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
