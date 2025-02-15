from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.api.helpers.custom_http_exception import CustomHTTPException
from app.database.config.session import SessionLocal


class BaseCrud:

    def __init__(self, db: Session, Model=None):
        self.db = db
        self.obj = None
        self.Model = Model

    def missing_obj(self, obj, _id=0):
        if obj is None:
            raise HTTPException(
                status_code=404, detail=f"Object with id {_id} not found.")

    def pagination(self, query, page=1, page_size=10):
        if page_size:
            query = query.limit(page_size)
        if page - 1:
            query = query.offset((page-1)*page_size)
        return query.all()

    def pagination_query(self, query, page: int = 1, page_size: int = 10):
        if page_size:
            query = query.limit(page_size)
        if page - 1:
            query = query.offset((page-1)*page_size)
        return query

    def get(self, id: int):
        self.obj = self.db.query(self.Model).filter(
            self.Model.id == id).first()
        self.missing_obj(self.obj, id)
        return self.obj

    def create_many(self, data_list):
        obj_list = [self.Model(**data) for data in data_list]
        obj = self.db.add_all(obj_list)
        self.db.commit()
        return obj

    # def search(self, query: str, page: int = 1, page_size: int = 10):
    #     query = sa.select(self.Model.c.title.match(query))
    #     query = self.pagination_query(query, page, page_size)
    #     return self.db.execute(query).scalars().all()

    def search(self, query: str, page: int = 1, page_size: int = 20):
        searchects = self.db.query(
            self.Model
        ).filter(
            self.Model.name.match(query)
        ).order_by(
            sa.desc(self.Model.modified_at)
        )
        return self.pagination(searchects, page, page_size)

    def get_all(self, page=0, page_size=10):
        query = self.db.query(self.Model).filter().order_by(
            sa.desc(self.Model.modified_at))
        return self.pagination(query, page, page_size)

    def commit(self, obj):
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def create(self, data: dict):
        obj = self.Model(**data)
        self.db.add(obj)
        return self.commit(obj)

    def update(self, data: dict):
        obj = self.get(data['id'])
        return self.update_obj(obj, data)

    def update_obj(self, obj, data: dict):
        self.missing_obj(obj, data.get('id', 0))
        if 'id' in data: data.pop('id')
        for key, value in data.items():
            setattr(obj, key, value)
        self.commit(obj)
        return obj

    def delete(self, id: int):
        obj = self.get(id)
        return self.delete_obj(obj)
    
    def delete_obj(self, obj):
        self.missing_obj(obj)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        
