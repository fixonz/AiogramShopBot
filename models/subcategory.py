from sqlalchemy import Integer, Column, String, Float, Boolean, ForeignKey

from models.base import Base


class Subcategory(Base):
    __tablename__ = 'subcategories'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    is_hidden = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
