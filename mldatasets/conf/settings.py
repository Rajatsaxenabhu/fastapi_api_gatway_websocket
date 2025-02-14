import os
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings
from decouple import config
from sqlalchemy import URL


def sql_db_uri(drivername, username, password, host, port, database):
    db_url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    return db_url


class Settings(BaseSettings):

    DEBUG: bool
    ENV: str

    APP_URL: str = "https://aiecobackend.instavivai.com"

    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_DB: str

    CELERY_BROKER_URL:str
    CELERY_RESULT_BACKEND:str

    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_POOL_SIZE: int = 1
    POSTGRES_MAX_POOL: int = 2
    POSTGRES_ENGINE_ECHO: bool = False
    SQLALCHEMY_DATABASE_URL_LOCAL: AnyHttpUrl = Field((
        "sqlite:///sql.db"),  validate_default=False)  # if DEV is local

    SQLALCHEMY_DATABASE_URL_DEV: AnyHttpUrl = Field(sql_db_uri(
        drivername='postgresql+psycopg2',
        username=config("POSTGRES_USER", cast=str),
        password=config('POSTGRES_PASSWORD', cast=str),
        host=config("POSTGRES_HOST", cast=str),
        port=config("POSTGRES_PORT", cast=int),
        database=config("POSTGRES_DB", cast=str)
    ),  validate_default=False)

    # development database if DEBUG is True
    SQLALCHEMY_DATABASE_URL_PROD: AnyHttpUrl = Field(sql_db_uri(
        drivername='postgresql+psycopg2',
        username=config("POSTGRES_USER"),
        password=config('POSTGRES_PASSWORD'),
        host=config("POSTGRES_HOST"),
        port=config("POSTGRES_PORT"),
        database=config("POSTGRES_DB")
    ),  validate_default=False)

    class Config:
        env_file = '.env'


settings = Settings()
