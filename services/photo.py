from pathlib import Path

from aiogram import Bot
from sqlalchemy import select

from db import get_db_session, session_refresh, session_commit, session_execute
from models.item import Item
from models.photo import Photo


class PhotoService:
    @staticmethod
    async def add_single(photo_path: str) -> int:
        async with get_db_session() as session:
            with open(photo_path, 'rb') as f:
                photo = Photo(
                    data=f.read()
                )
                session.add(photo)
                await session_commit(session)
                await session_refresh(session, photo)
                return photo.id

    @staticmethod
    async def add_from_file_id(file_id: str, bot: Bot):
        file = await bot.get_file(file_id)
        photo_path = f"photos/{file.file_unique_id}.jpg"
        await bot.download_file(file.file_path, photo_path)
        photo_id = await PhotoService.add_single(photo_path)
        Path(photo_path).unlink(missing_ok=True)
        return photo_id
