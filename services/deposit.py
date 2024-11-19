import datetime
from typing import List
from sqlalchemy import select
from db import session_execute, session_commit, session_refresh, get_db_session
from models.deposit import Deposit


class DepositService:

    @staticmethod
    async def create(tx_id, user_id, network, amount, vout=None):
        async with get_db_session() as session:
            dep = Deposit(user_id=user_id,
                          tx_id=tx_id,
                          network=network,
                          amount=amount,
                          vout=vout)
            session.add(dep)
            await session_commit(session)
            await session_refresh(session, dep)
            return dep.id

    @staticmethod
    async def get_by_user_id(user_id: int):
        async with get_db_session() as session:
            stmt = select(Deposit).where(Deposit.user_id == user_id)
            deposits = await session_execute(stmt, session)
            deposits = deposits.scalars().all()
            return deposits

    @staticmethod
    async def get_by_timedelta(timedelta_int: int) -> List[Deposit]:
        current_time = datetime.datetime.now()
        timedelta = datetime.timedelta(days=int(timedelta_int))
        time_to_subtract = current_time - timedelta
        async with get_db_session() as session:
            stmt = select(Deposit).where(Deposit.deposit_datetime >= time_to_subtract)
            deposits = await session_execute(stmt, session)
            return deposits.scalars().all()

    @staticmethod
    async def get_by_id(deposit_id: int) -> Deposit:
        async with get_db_session() as session:
            stmt = select(Deposit).where(Deposit.id == deposit_id)
            deposit = await session_execute(stmt, session)
            return deposit.scalar()

