from sqlalchemy import Column, Integer, LargeBinary

from models.base import Base


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True, unique=True)
    data = Column(LargeBinary, nullable=False)
