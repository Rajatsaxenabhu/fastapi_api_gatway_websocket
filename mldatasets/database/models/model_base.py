import datetime
from uuid import uuid4

import inflect
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    id = Column(Integer, primary_key=True, unique=True,
                index=True, autoincrement=True)
    # uid = Column(UUID(as_uuid=True), index=True, default=uuid4, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    modified_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )
    __name__: str

    # Internal Method to generate table name
    def _generate_table_name(str):
        words = [[str[0]]]
        for c in str[1:]:
            if words[-1][-1].islower() and c.isupper():
                words.append(list(c))
            else:
                words[-1].append(c)
        return inflect.engine().plural(
            "_".join("".join(word) for word in words).lower()
        )

    # Generate __tablename__ automatically in plural form.

    # i.e 'myTable' model will generate table name 'my_tables'
    @declared_attr
    def __tablename__(cls) -> str:
        return cls._generate_table_name(cls.__name__)
