import os 
import uuid
import shutil
from pathlib import Path
from fastapi import status, HTTPException
from conf.db_config import pg_session_dependency
import json
from database.crud.crud import MLDatasetCrud,MLDatasetFolderCrud, MLDatasetFilesCrud
from fastapi_api_gateway.api_gateway.mldatasets.schema.ml_schema import MLDatasetSchema, MLDatasetFolderSchema
import shutil
static_dir = "static/mldatabase"
os.makedirs(static_dir, exist_ok=True)

class MLDatasetService:
    @staticmethod
    def create_database(payload:MLDatasetSchema,db:pg_session_dependency):
        try:
            unique_end=uuid.uuid4().hex[:8]
            unique_name=f"{payload.name}_{unique_end}"
            unique_path=Path(static_dir)/unique_name
            try:
                unique_path.mkdir(parents=True,exist_ok=False)
            except FileExistsError:
                return False,"dataset is already created please retry"
            new_payload={
                "name":payload.name,
                "path":str(unique_path),
                "storage": payload.storage,
                "visible":payload.visible
            }
            print("phase2")
            print(new_payload)
            try:
                obj=MLDatasetCrud(db).create_folder(new_payload)
                print("obj is generated",obj)
                print("Object contents:", obj.__dict__ if hasattr(obj, '__dict__') else obj)
                return True,obj
            except Exception as e:
                return False,f"unexcepted error is {str(e)}"
        except Exception as err:
            return False,f"unexcepted error is {str(err)}"
        
    @staticmethod  
    def create_folder(payload:MLDatasetFolderSchema,db:pg_session_dependency):
        try:
            obj=None
            if payload.dataset_id == 0:
                obj=MLDatasetFolderCrud(db).get(payload.parent_folder_id)
            if payload.parent_folder_id == 0:
                obj=MLDatasetCrud(db).get(payload.dataset_id)
            if obj is None:
                detail="dataset not found" if payload.dataset_id is not None else "folder not found"
                return False,detail
            print("phase1")
            unique_end=uuid.uuid4().hex[:8]
            unique_name=f"{payload.name}_{unique_end}"
            unique_path=Path(obj.path)/unique_name
            print("phase2")
            try:
                unique_path.mkdir(parents=True,exist_ok=False)
            except FileExistsError:
                return False,"folder is already created please retry"
            print("phase3")
            new_payload={
                'name':payload.folder_name,
                'path':str(unique_path),
                'dataset_id':payload.dataset_id,
                'parent_folder_id':payload.parent_folder_id               
            }
            print("phase4")
            if payload.parent_folder_id == 0:
                del new_payload['parent_folder_id']
            if payload.dataset_id == 0:
                del new_payload['dataset_id']
            obj=MLDatasetFolderCrud(db).create_folder(new_payload)
            print('send before [ay;oad]',obj)
            print("phase5")
            return True,obj
        except Exception as err:
            return False,f"unexcepted error is {str(err)}"

    @staticmethod        
    def delete_database(Id:int,db:pg_session_dependency):
        try:
            obj_path=MLDatasetCrud(db).get(Id)
            print("obj_path",obj_path)
            print("pahse 1")
            if not os.path.exists(obj_path.path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder with this path  not found")
            shutil.rmtree(obj_path.path)
            obj=MLDatasetCrud(db).get(Id)
            if obj is None:
                return False
            obj=MLDatasetCrud(db).delete_dataset(Id)
            return True
        except Exception as e:
            print('error in delete dataset',(e))
            raise HTTPException(status_code=404,detail="Dataset not found")
            
    @staticmethod
    def delete_folder(id:int,db:pg_session_dependency):
        try:
            if MLDatasetFolderCrud(db).delete(id):
                return True
        except Exception as e:
            print(e)
            return False
    
    @staticmethod
    def check_payload(payload:str):
        try:
            new_payload=json.loads(payload)
            new_payload['dataset_id']=None if new_payload['dataset_id']==0 else new_payload['dataset_id']
            
            new_payload['dataset_folder_id']=None if new_payload['dataset_folder_id']==0 else new_payload['dataset_folder_id']
            if new_payload['dataset_id'] is None and new_payload['dataset_folder_id'] is None:
                raise ValueError("dataset folder id and dataset id must be greater than 0")
            if new_payload['dataset_id'] is not None and new_payload['dataset_folder_id'] is not None:
                raise ValueError("cannot gave both a dataset and a parent folder id")
            return new_payload
        except:
            return False

    @staticmethod 
    def create_files(db:pg_session_dependency,payload:any,files:any):
        try:
            dataset_id = payload.get('dataset_id')
            folder_id = payload.get('dataset_folder_id')
            if dataset_id is None:
                obj = MLDatasetFolderCrud(db).get(folder_id)
            else:
                obj = MLDatasetCrud(db).get(dataset_id)

            if obj is None:
                return False,f"dataset or folder not found"
            obj1=MLDatasetFilesCrud(db)
            for file in files:
                target_path = Path(obj.path)
                os.makedirs(str(target_path), exist_ok=True)
                file_location = Path(target_path).joinpath(file.filename)
                with file_location.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                file_payload={
                    "file_name":file.filename,
                    "file_path":str(file_location),
                    "dataset_id":payload.get('dataset_id'),
                    "dataset_folder_id":payload.get('dataset_folder_id'),
                    "content_type":file.content_type,
                    "file_size":file.size
                }
                obj1.upload_file(file_payload)
            return True,f"files uploaded successfully"
        except Exception as err:
            print(err)
            return False