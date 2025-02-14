from typing import Annotated

from fastapi import Depends
from session import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends

from sqlalchemy.orm import Session


class PostgresDb():
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                PostgresDb, cls).__new__(cls, *args, **kwargs)
            cls._instances[cls]._session = SessionLocal()
        return cls._instances[cls]

    def session(self) -> Session:
        return self._session

pg_session_dependency = Annotated[Session, Depends(PostgresDb().session)]
db_dependency = pg_session_dependency