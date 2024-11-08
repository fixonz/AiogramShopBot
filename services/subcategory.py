import math
from sqlalchemy import select, func, delete, update
import config
from db import session_commit, session_execute, session_refresh, get_db_session
from models.item import Item
from models.photo import Photo
from models.subcategory import Subcategory


class SubcategoryService:

    @staticmethod
    async def get_or_create_one(subcategory_name: str, price: float, category_id: int, image_id: int) -> Subcategory:
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.name == subcategory_name,
                                             Subcategory.price == price,
                                             Subcategory.category_id == category_id)
            subcategory = await session_execute(stmt, session)
            subcategory = subcategory.scalar()
            if subcategory is None:
                new_category_obj = Subcategory(name=subcategory_name, price=price, category_id=category_id,
                                               image_id=image_id)
                session.add(new_category_obj)
                await session_commit(session)
                await session_refresh(session, new_category_obj)
                return new_category_obj
            else:
                stmt = update(Subcategory).where(Subcategory.name == subcategory.name).values(price=price,
                                                                                              image_id=image_id,
                                                                                              is_hidden=False,
                                                                                              category_id=category_id)
                await session_execute(stmt, session)
                await session_commit(session)
                await session_refresh(session, subcategory)
                return subcategory

    @staticmethod
    async def get_to_delete(page: int = 0) -> list[Subcategory]:
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.is_hidden == 0).distinct().limit(config.PAGE_ENTRIES).offset(
                page * config.PAGE_ENTRIES).group_by(Subcategory.name)
            subcategories = await session_execute(stmt, session=session)
            subcategories = subcategories.scalars().all()
            return subcategories

    @staticmethod
    async def get_maximum_page():
        async with get_db_session() as session:
            stmt = select(func.count(Subcategory.id)).distinct()
            subcategories = await session_execute(stmt, session)
            subcategories_count = subcategories.scalar_one()
            if subcategories_count % config.PAGE_ENTRIES == 0:
                return subcategories_count / config.PAGE_ENTRIES - 1
            else:
                return math.trunc(subcategories_count / config.PAGE_ENTRIES)

    @staticmethod
    async def get_maximum_page_to_delete():
        async with get_db_session() as session:
            unique_categories_subquery = (
                select(Subcategory.id)
                .filter(Subcategory.is_hidden == 0)
                .distinct()
            ).alias('unique_categories')
            stmt = select(func.count()).select_from(unique_categories_subquery)
            max_page = await session_execute(stmt, session)
            max_page = max_page.scalar_one()
            if max_page % config.PAGE_ENTRIES == 0:
                return max_page / config.PAGE_ENTRIES - 1
            else:
                return math.trunc(max_page / config.PAGE_ENTRIES)

    @staticmethod
    async def get_by_primary_key(subcategory_id: int) -> Subcategory:
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.id == subcategory_id)
            subcategory = await session_execute(stmt, session)
            return subcategory.scalar()

    @staticmethod
    async def delete_if_not_used(subcategory_id: int):
        # TODO("Need testing")
        async with get_db_session() as session:
            stmt = select(Subcategory).join(Item, Item.subcategory_id == subcategory_id).where(
                Subcategory.id == subcategory_id)
            result = await session_execute(stmt, session)
            if result.scalar() is None:
                stmt = delete(Subcategory).where(Subcategory.id == subcategory_id)
                await session_execute(stmt, session)
                await session_commit(session)

    @staticmethod
    async def get_by_category_id(page: int, category_id: int):
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.is_hidden == False,
                                             Subcategory.category_id == category_id).limit(config.PAGE_ENTRIES).offset(
                page * config.PAGE_ENTRIES).group_by(
                Subcategory.name)
            subcategories = await session_execute(stmt, session)
            return subcategories.scalars().all()

    @staticmethod
    async def get_all(page: int):
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.is_hidden == False).limit(config.PAGE_ENTRIES).offset(
                page * config.PAGE_ENTRIES).group_by(
                Subcategory.name)
            subcategories = await session_execute(stmt, session)
            return subcategories.scalars().all()

    @staticmethod
    async def get_price_by_subcategory(subcategory_id: int) -> float:
        async with get_db_session() as session:
            stmt = select(Subcategory.price).where(Subcategory.id == subcategory_id)
            price = await session_execute(stmt, session)
            return price.scalar()

    @staticmethod
    async def set_hidden(subcategory_id: int):
        async with get_db_session() as session:
            stmt = update(Subcategory).where(Subcategory.id == subcategory_id).values(is_hidden=True)
            await session_execute(stmt, session)
            await session_commit(session)

    @staticmethod
    async def update(sucategory_id: int, values_dict: dict):
        async with get_db_session() as session:
            stmt = update(Subcategory).where(Subcategory.id == sucategory_id).values(**values_dict)
            await session_execute(stmt, session)
            await session_commit(session)

    @staticmethod
    async def get_photo(subcategory_id: int) -> Photo:
        async with get_db_session() as session:
            stmt = select(Photo).join(Subcategory, Subcategory.image_id == Photo.id).where(
                Subcategory.id == subcategory_id)
            photo = await session_execute(stmt, session)
            return photo.scalar()
