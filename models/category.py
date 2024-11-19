from sqlalchemy import Integer, Column, String, ForeignKey, Boolean

from models.base import Base


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    image_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    is_hidden = Column(Boolean, default=False)
