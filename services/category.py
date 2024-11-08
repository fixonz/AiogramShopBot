import math
from sqlalchemy import select, func, update
import config
from models.category import Category
from models.item import Item
from db import session_commit, session_execute, session_refresh, get_db_session
from models.photo import Photo
from models.subcategory import Subcategory


class CategoryService:

    @staticmethod
    async def get_or_create_one(category_name: str, description: str, image_id: int) -> Category:
        async with get_db_session() as session:
            stmt = select(Category).where(Category.name == category_name,
                                          Category.description == description)
            category = await session_execute(stmt, session)
            category = category.scalar()
            if category is None:
                new_category_obj = Category(name=category_name, description=description, image_id=image_id)
                session.add(new_category_obj)
                await session_commit(session)
                await session_refresh(session, new_category_obj)
                return new_category_obj
            else:
                stmt = update(Category).where(Category.name == category.name).values(description=description,
                                                                                     image_id=image_id, is_hidden=False)
                await session_execute(stmt, session)
                await session_commit(session)
                await session_refresh(session, category)
                return category

    @staticmethod
    async def get_by_primary_key(primary_key: int) -> Category:
        async with get_db_session() as session:
            stmt = select(Category).where(Category.id == primary_key)
            category = await session_execute(stmt, session)
            return category.scalar()

    @staticmethod
    async def get_to_hide(page: int = 0):
        async with get_db_session() as session:
            stmt = select(Category).where(Category.is_hidden == 0).distinct().limit(config.PAGE_ENTRIES).offset(
                page * config.PAGE_ENTRIES).group_by(Category.name)
            categories = await session_execute(stmt, session)
            return categories.scalars().all()

    @staticmethod
    async def have_items(category_id: int) -> int:
        async with get_db_session() as session:
            sub_stmt = select(Item.id).join(Subcategory, Item.subcategory_id == Subcategory.id).join(Category,
                                                                                                     Subcategory.category_id == Category.id).where(
                Item.is_sold == 0, Category.id == category_id)
            stmt = select(func.count()).select_from(sub_stmt)
            category_names = await session_execute(stmt, session)
            return category_names.scalar()

    @staticmethod
    async def get_maximum_page_to_delete() -> int:
        async with get_db_session() as session:
            unique_categories_subquery = (
                select(Category.id)
                .filter(Category.is_hidden == 0)
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
    async def get_maximum_page() -> int:
        async with get_db_session() as session:
            stmt = select(func.count(Category.id)).distinct()
            subcategories = await session_execute(stmt, session)
            subcategories_count = subcategories.scalar_one()
            if subcategories_count % config.PAGE_ENTRIES == 0:
                return subcategories_count / config.PAGE_ENTRIES - 1
            else:
                return math.trunc(subcategories_count / config.PAGE_ENTRIES)

    @staticmethod
    async def get_all(page: int):
        async with get_db_session() as session:
            stmt = select(Category).where(Category.is_hidden == False).limit(config.PAGE_ENTRIES).offset(
                page * config.PAGE_ENTRIES).group_by(
                Category.name)
            categories = await session_execute(stmt, session)
            return categories.scalars().all()

    @staticmethod
    async def get_photo(category_id: int) -> Photo:
        async with get_db_session() as session:
            stmt = select(Photo).join(Category, Category.image_id == Photo.id).where(Category.id == category_id)
            photo = await session_execute(stmt, session)
            return photo.scalar()

    @staticmethod
    async def get_description(category_id: int) -> str:
        async with get_db_session() as session:
            stmt = select(Category.description).where(Category.id == category_id).limit(1)
            description = await session_execute(stmt, session)
            return description.scalar()

    @staticmethod
    async def set_hidden(category_id: int):
        async with get_db_session() as session:
            stmt = update(Category).where(Category.id == category_id).values(is_hidden=True)
            await session_execute(stmt, session)
            await session_commit(session)

    @staticmethod
    async def update(category_id: int, values_dict: dict):
        async with get_db_session() as session:
            stmt = update(Category).where(Category.id == category_id).values(**values_dict)
            await session_execute(stmt, session)
            await session_commit(session)

    @staticmethod
    async def get_by_subcategory_id(subcategory_id: int):
        async with get_db_session() as session:
            stmt = select(Category).join(Subcategory, Subcategory.category_id == Category.id).where(Subcategory.id == subcategory_id)
            category = await session_execute(stmt, session)
            return category.scalar()
