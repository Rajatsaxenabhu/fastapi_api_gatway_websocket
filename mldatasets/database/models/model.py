from sqlalchemy import String
from sqlalchemy.orm import mapped_column,Mapped,backref,remote
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import List,Literal
import sqlalchemy as sa
from mldatasets.database.crud.crud import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship,backref,Mapped
from sqlalchemy import String, ForeignKey, Integer
storage_location=Literal['local','cloud']

class MLDataset(Base):
    __tablename__ = 'ml_dataset'
    name: Mapped[str] = mapped_column(String(50))
    path: Mapped[str] = mapped_column(String(255))

    ml_folders: Mapped[List["MLDatasetFolder"]] = relationship(
        "MLDatasetFolder",
        back_populates="ml_dataset",
        cascade="all, delete-orphan"
    )
    
    ml_folder_files: Mapped[List["MLDatasetFiles"]] = relationship(
        "MLDatasetFiles",
        back_populates="ml_dataset",
        cascade="all, delete-orphan"
    )
    
    storage: Mapped[storage_location] = mapped_column(String(20))  # local, cloud
    visible: Mapped[str] = mapped_column(String(50),nullable=True)  # public/aws


class MLDatasetFolder(Base):
    __tablename__ = 'ml_dataset_folder'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    path: Mapped[str] = mapped_column(String(255))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("ml_dataset.id"), nullable=True)
    parent_folder_id: Mapped[int] = mapped_column(ForeignKey("ml_dataset_folder.id"), nullable=True)
    
    # Relationship with dataset
    ml_dataset: Mapped["MLDataset"] = relationship(
        "MLDataset",
        back_populates="ml_folders"
    )
    
    # Relationship with files
    ml_folder_files: Mapped[List["MLDatasetFiles"]] = relationship(
        "MLDatasetFiles",
        back_populates="ml_dataset_folder",
        cascade="all, delete-orphan"
    )
    
    # Self-referential relationship for folder hierarchy
    parent_folder: Mapped["MLDatasetFolder"] = relationship(
        "MLDatasetFolder",
        remote_side=[id],
        backref=backref("child_folders", cascade="all, delete-orphan",lazy="select"),
    )

class MLDatasetFiles(Base):
    __tablename__ = 'ml_dataset_files'
    file_name: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[str] = mapped_column(String(10))  # in MB
    content_type: Mapped[str] = mapped_column(String(20))  # img, file, audio, etc.

    dataset_id: Mapped[int] = mapped_column(ForeignKey("ml_dataset.id"), nullable=True)
    dataset_folder_id: Mapped[int] = mapped_column(ForeignKey("ml_dataset_folder.id"), nullable=True)

    ml_dataset: Mapped["MLDataset"] = relationship(
        "MLDataset",
        back_populates="ml_folder_files"
    )
    ml_dataset_folder: Mapped["MLDatasetFolder"] = relationship(
        "MLDatasetFolder",
        back_populates="ml_folder_files"
    )

class AlgorithmBlogMixin:
    title = sa.Column(sa.String(64), nullable=False)
    acuracy = sa.Column(JSONB)
    visible = sa.Column(sa.String(16), default='public')
    

class Algorithm(Base,AlgorithmBlogMixin):
    __tablename__ = 'algorithms'

    # TODO: Define reverse relationship with models
    models:Mapped["Models"] = relationship("Models",backref=backref("modal_algorithms"))
    blog:Mapped[List["Blog"]] = relationship("Blog",backref=backref("blog_algorithms"))



class Models(Base,AlgorithmBlogMixin):
    __tablename__ = 'models'
    algorithm_id = sa.Column(sa.Integer,sa.ForeignKey('algorithms.id',ondelete='CASCADE'),nullable=False)
    ml_dataset_id = sa.Column(sa.Integer,sa.ForeignKey('ml_dataset.id',ondelete='CASCADE'),nullable=False)

    # TODO: Define reverse relationship
    algorithm:Mapped["Algorithm"] = relationship("Algorithm",backref=backref('algorithms_models'),passive_deletes=True)
    blog:Mapped["Blog"] = relationship("Blog",backref=backref("blog_models"))
    ml_dataset:Mapped["MLDataset"] = relationship("MLDataset",backref=backref("ml_dataset_models"))

class Blog(Base):
    __tablename__ = 'blogs'
    title = sa.Column(sa.String(64), nullable=False)
    description = sa.Column(sa.TEXT)
    published = sa.Column(sa.Boolean, default=True)
    algorithm_id = sa.Column(sa.Integer,sa.ForeignKey('algorithms.id',ondelete='CASCADE'),nullable=True)
    model_id = sa.Column(sa.Integer,sa.ForeignKey('models.id',ondelete='CASCADE'),nullable=True)

    # TODO: Define reverse relationship
    # algorithm:Mapped["Algorithm"]  = relationship("Algorithm", backref=backref('algorithms_blogs'),passive_deletes=True)
    # model:Mapped["Models"] = relationship("Models", backref=backref('models_blog'),passive_deletes=True)