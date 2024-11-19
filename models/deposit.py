from sqlalchemy import Integer, Column, String, ForeignKey, Boolean, BigInteger, DateTime, func, Float

from models.base import Base


class Deposit(Base):
    __tablename__ = 'deposits'
    id = Column(Integer, primary_key=True)
    tx_id = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    network = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)
    is_withdrawn = Column(Boolean, default=False)
    vout = Column(Integer, nullable=True)
    deposit_datetime = Column(DateTime, default=func.now())
