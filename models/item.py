from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

from models.base import Base


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, unique=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), nullable=False)
    subcategory = relationship("Subcategory", backref=backref("subcategories", cascade="all"), passive_deletes="all",
                               lazy="joined")
    private_data = Column(String, nullable=False, unique=False)
    is_sold = Column(Boolean, nullable=False, default=False)
    is_new = Column(Boolean, nullable=False, default=True)


@dataclass
class ItemDTO:
    category: str
    subcategory: str
    private_data: str
    price: float
    description: str
