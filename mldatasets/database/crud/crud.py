from api_gateway.mldatasets.database.crud.base import BaseCrud

from sqlalchemy.orm import Session
import sqlalchemy as sa 
from sqlalchemy import select
from mldatasets.database.models.model import MLDataset,MLDatasetFiles,MLDatasetFolder
from sqlalchemy.orm import Session


class MLDatasetCrud(BaseCrud):
    def __init__(self, db_session: Session):
        super().__init__(db_session,MLDataset)
    
    def create_folder(self,payload:dict):
        return self.create(payload)
    
    # def get_all_folder(self,page,page_size):
    #     columns_to_select = [getattr(self.Model, column) for column in self.Model.__table__.columns.keys() if column !='path']
    #     query = self.db.query(*columns_to_select).filter().order_by(sa.desc(self.Model.modified_at))
    #     return self.pagination(query, page, page_size)
    def get_all_dataset(self, page=0, page_size=10):
        return super().get_all(page, page_size)
    
    def get_dataset(self,id):
        return  self.get(id)
    
    def delete_dataset(self,id):
        return self.delete(id)
    
class MLDatasetFolderCrud(BaseCrud):
    def __init__(self, db_session: Session):
        super().__init__(db_session,MLDatasetFolder)
    
    def create_folder(self,payload:dict):
        return self.create(payload)

class MLDatasetFilesCrud(BaseCrud):
    def __init__(self, db_session: Session):
        super().__init__(db_session,MLDatasetFiles)
    
    def upload_file(self,payload:dict):
        return self.create(payload)
