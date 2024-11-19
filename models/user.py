from sqlalchemy import Column, Integer, DateTime, String, Boolean, Float, func, ForeignKey

from models.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_username = Column(String, unique=True)
    telegram_id = Column(Integer, nullable=False, unique=True)
    last_balance_refresh = Column(DateTime)
    top_up_amount = Column(Float, default=0.0)
    consume_records = Column(Float, default=0.0)
    registered_at = Column(DateTime, default=func.now())
    can_receive_messages = Column(Boolean, default=True)
    ltc_address = Column(String, nullable=False, unique=True)
    ltc_balance = Column(Float, default=0.0)
    seed = Column(String, nullable=False, unique=True)
