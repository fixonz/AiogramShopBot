from typing import Union

from aiogram import types, Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from handlers.common.common import add_pagination_buttons
from services.buy import BuyService
from services.buyItem import BuyItemService
from services.category import CategoryService
from services.item import ItemService
from services.subcategory import SubcategoryService
from services.user import UserService
from utils.custom_filters import IsUserExistFilter
from utils.localizator import Localizator, BotEntity
from utils.notification_manager import NotificationManager


class AllCategoriesCallback(CallbackData, prefix="all_categories"):
    level: int
    category_id: int
    subcategory_id: int
    price: float
    quantity: int
    total_price: float
    confirmation: bool
    page: int


def create_callback_all_categories(level: int,
                                   category_id: int = -1,
                                   subcategory_id: int = -1,
                                   price: float = 0.0,
                                   total_price: float = 0.0,
                                   quantity: int = 1,
                                   confirmation: bool = False,
                                   page: int = 0):
    return AllCategoriesCallback(level=level, category_id=category_id, subcategory_id=subcategory_id, price=price,
                                 total_price=total_price,
                                 quantity=quantity, confirmation=confirmation, page=page).pack()


all_categories_router = Router()


@all_categories_router.message(F.text == Localizator.get_text(BotEntity.USER, "all_categories"),
                               IsUserExistFilter())
async def all_categories_text_message(message: types.message):
    await all_categories(message)


async def create_category_buttons(page: int):
    categories = await CategoryService.get_all(page)
    if categories:
        categories_builder = InlineKeyboardBuilder()
        for category in categories:
            items_count = await CategoryService.have_items(category.id)
            if items_count > 0:
                categories_builder.button(text=f"✅ {category.name}",
                                          callback_data=create_callback_all_categories(level=1,
                                                                                       category_id=category.id))
            else:
                categories_builder.button(text=f"❌ {category.name}",
                                          callback_data=create_callback_all_categories(level=1,
                                                                                       category_id=category.id))
        categories_builder.adjust(2)
        return categories_builder


async def create_subcategory_buttons(category_id: int, page: int = 0):
    current_level = 1
    items = await ItemService.get_unsold_subcategories_by_category(category_id, page)
    subcategories_builder = InlineKeyboardBuilder()
    for item in items:
        subcategory_price = await SubcategoryService.get_price_by_subcategory(item.subcategory_id)
        available_quantity = await ItemService.get_available_quantity(item.subcategory_id)
        subcategory_inline_button = create_callback_all_categories(level=current_level + 1,
                                                                   category_id=category_id,
                                                                   subcategory_id=item.subcategory_id,
                                                                   price=subcategory_price)
        subcategories_builder.button(
            text=Localizator.get_text(BotEntity.USER, "subcategory_button").format(
                subcategory_name=item.subcategory.name,
                subcategory_price=subcategory_price,
                available_quantity=available_quantity,
                currency_sym=Localizator.get_currency_symbol()),
            callback_data=subcategory_inline_button)
    subcategories_builder.adjust(1)
    return subcategories_builder


async def all_categories(message: Union[Message, CallbackQuery]):
    if isinstance(message, Message):
        category_inline_buttons = await create_category_buttons(0)
        zero_level_callback = create_callback_all_categories(0)
        if category_inline_buttons:
            category_inline_buttons = await add_pagination_buttons(category_inline_buttons, zero_level_callback,
                                                                   CategoryService.get_maximum_page_to_delete(),
                                                                   AllCategoriesCallback.unpack, None)
            await message.answer(Localizator.get_text(BotEntity.USER, "all_categories"),
                                 reply_markup=category_inline_buttons.as_markup())
        else:
            await message.answer(Localizator.get_text(BotEntity.USER, "no_categories"))
    elif isinstance(message, CallbackQuery):
        callback = message
        unpacked_callback = AllCategoriesCallback.unpack(callback.data)
        category_inline_buttons = await create_category_buttons(unpacked_callback.page)
        if category_inline_buttons:
            category_inline_buttons = await add_pagination_buttons(category_inline_buttons, callback.data,
                                                                   CategoryService.get_maximum_page_to_delete(),
                                                                   AllCategoriesCallback.unpack, None)
            await callback.message.delete()
            await callback.message.answer(Localizator.get_text(BotEntity.USER, "all_categories"),
                                          reply_markup=category_inline_buttons.as_markup())
        else:
            await callback.message.delete()
            await callback.message.answer(Localizator.get_text(BotEntity.USER, "no_categories"))


async def show_subcategories_in_category(callback: CallbackQuery):
    unpacked_callback = AllCategoriesCallback.unpack(callback.data)
    subcategory_buttons = await create_subcategory_buttons(unpacked_callback.category_id, page=unpacked_callback.page)
    back_button = types.InlineKeyboardButton(
        text=Localizator.get_text(BotEntity.USER, "back_to_all_categories"),
        callback_data=create_callback_all_categories(
            level=unpacked_callback.level - 1))
    if len(subcategory_buttons.as_markup().inline_keyboard) == 0:
        await callback.message.edit_text(Localizator.get_text(BotEntity.USER, "no_subcategories"),
                                         reply_markup=subcategory_buttons.row(back_button).as_markup())
    else:
        subcategory_buttons = await add_pagination_buttons(subcategory_buttons, callback.data,
                                                           ItemService.get_maximum_page(unpacked_callback.category_id),
                                                           AllCategoriesCallback.unpack,
                                                           back_button)
        category_photo = await CategoryService.get_photo(unpacked_callback.category_id)
        category = await CategoryService.get_by_primary_key(unpacked_callback.category_id)
        user = await UserService.get_by_tgid(callback.from_user.id)
        balance = user.top_up_amount - user.consume_records
        media = types.InputMediaPhoto(media=BufferedInputFile(category_photo.data,
                                                              f"{category_photo.id}.jpg"),
                                      caption=Localizator.get_text(BotEntity.USER,
                                                                   "subcategories").format(
                                          category_name=category.name,
                                          description=category.description,
                                          user_balance=balance,
                                          currency_text=Localizator.get_currency_text()
                                      ))
        await callback.message.edit_media(media=media, reply_markup=subcategory_buttons.as_markup())


async def buy_confirmation(callback: CallbackQuery):
    unpacked_callback = AllCategoriesCallback.unpack(callback.data)
    price = unpacked_callback.price
    total_price = unpacked_callback.price * unpacked_callback.quantity
    subcategory_id = unpacked_callback.subcategory_id
    category_id = unpacked_callback.category_id
    current_level = unpacked_callback.level
    quantity = unpacked_callback.quantity
    description = await CategoryService.get_description(category_id)
    confirmation_builder = InlineKeyboardBuilder()
    confirm_button_callback = create_callback_all_categories(level=current_level + 1,
                                                             category_id=category_id,
                                                             subcategory_id=subcategory_id,
                                                             price=price,
                                                             total_price=total_price,
                                                             quantity=quantity,
                                                             confirmation=True)
    decline_button_callback = create_callback_all_categories(level=current_level + 1,
                                                             category_id=category_id,
                                                             subcategory_id=subcategory_id,
                                                             price=price,
                                                             total_price=total_price,
                                                             quantity=quantity,
                                                             confirmation=False)
    confirmation_button = types.InlineKeyboardButton(text=Localizator.get_text(BotEntity.COMMON, "confirm"),
                                                     callback_data=confirm_button_callback)
    decline_button = types.InlineKeyboardButton(text=Localizator.get_text(BotEntity.COMMON, "cancel"),
                                                callback_data=decline_button_callback)
    back_button = types.InlineKeyboardButton(text=Localizator.get_text(BotEntity.COMMON, "back_button"),
                                             callback_data=create_callback_all_categories(level=current_level - 1,
                                                                                          category_id=category_id,
                                                                                          subcategory_id=subcategory_id,
                                                                                          price=price))
    confirmation_builder.add(confirmation_button, decline_button, back_button)
    confirmation_builder.adjust(2)
    subcategory = await SubcategoryService.get_by_primary_key(subcategory_id)
    category = await CategoryService.get_by_primary_key(category_id)
    user = await UserService.get_by_tgid(callback.from_user.id)
    balance = user.top_up_amount - user.consume_records
    await callback.message.delete()
    await callback.message.answer(
        text=Localizator.get_text(BotEntity.USER, "buy_confirmation").format(category_name=category.name,
                                                                             subcategory_name=subcategory.name,
                                                                             price=price,
                                                                             description=description,
                                                                             quantity=quantity,
                                                                             total_price=total_price,
                                                                             user_balance=balance,
                                                                             currency_sym=Localizator.get_currency_symbol()),
        reply_markup=confirmation_builder.as_markup())


async def select_quantity(callback: CallbackQuery):
    unpacked_callback = AllCategoriesCallback.unpack(callback.data)
    price = unpacked_callback.price
    subcategory_id = unpacked_callback.subcategory_id
    category_id = unpacked_callback.category_id
    current_level = unpacked_callback.level
    count_builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        count_builder.button(text=str(i), callback_data=create_callback_all_categories(level=current_level + 1,
                                                                                       category_id=category_id,
                                                                                       subcategory_id=subcategory_id,
                                                                                       price=price,
                                                                                       quantity=i,
                                                                                       total_price=price * i))
    count_builder.adjust(3)
    back_button = types.InlineKeyboardButton(text=Localizator.get_text(BotEntity.COMMON, "back_button"),
                                             callback_data=create_callback_all_categories(level=current_level - 1,
                                                                                          category_id=category_id))
    count_builder.row(back_button)
    subcategory = await SubcategoryService.get_by_primary_key(subcategory_id)
    category = await CategoryService.get_by_primary_key(category_id)
    available_qty = await ItemService.get_available_quantity(subcategory_id)
    subcategory_photo = await SubcategoryService.get_photo(subcategory_id)
    user = await UserService.get_by_tgid(callback.from_user.id)
    balance = user.top_up_amount - user.consume_records
    media = types.InputMediaPhoto(media=BufferedInputFile(subcategory_photo.data,
                                                          f"{subcategory_photo.id}.jpg"),
                                  caption=Localizator.get_text(BotEntity.USER,
                                                               "select_quantity").format(
                                      category_name=category.name,
                                      subcategory_name=subcategory.name,
                                      description=category.description,
                                      user_balance=balance,
                                      currency_sym=Localizator.get_currency_symbol(),
                                      price=subcategory.price,
                                      quantity=available_qty
                                  ))
    await callback.message.edit_media(media, reply_markup=count_builder.as_markup())


async def buy_processing(callback: CallbackQuery):
    unpacked_callback = AllCategoriesCallback.unpack(callback.data)
    confirmation = unpacked_callback.confirmation
    total_price = unpacked_callback.price * unpacked_callback.quantity
    subcategory_id = unpacked_callback.subcategory_id
    category_id = unpacked_callback.category_id
    quantity = unpacked_callback.quantity
    telegram_id = callback.from_user.id
    is_in_stock = await ItemService.get_available_quantity(subcategory_id) >= quantity
    is_enough_money = await UserService.is_buy_possible(telegram_id, total_price)
    back_to_main_builder = InlineKeyboardBuilder()
    back_to_main_callback = create_callback_all_categories(level=0)
    back_to_main_button = types.InlineKeyboardButton(
        text=Localizator.get_text(BotEntity.USER, "all_categories"),
        callback_data=back_to_main_callback)
    back_to_main_builder.add(back_to_main_button)
    bot = callback.bot
    if confirmation and is_in_stock and is_enough_money:
        await callback.message.delete()
        await UserService.update_consume_records(telegram_id, total_price)
        sold_items = await ItemService.get_bought_items(subcategory_id, quantity)
        user = await UserService.get_by_tgid(telegram_id)
        new_buy_id = await BuyService.insert_new(user, quantity, total_price)
        await BuyItemService.insert_many(sold_items, new_buy_id)
        await ItemService.set_items_sold(sold_items)
        await NotificationManager.new_buy(category_id, subcategory_id, quantity, total_price, user, bot)
    elif confirmation is False:
        await callback.message.edit_text(text=Localizator.get_text(BotEntity.COMMON, "cancelled"),
                                         reply_markup=back_to_main_builder.as_markup())
    elif is_enough_money is False:
        await callback.message.edit_text(text=Localizator.get_text(BotEntity.USER, "insufficient_funds"),
                                         reply_markup=back_to_main_builder.as_markup())
    elif is_in_stock is False:
        await callback.message.edit_text(text=Localizator.get_text(BotEntity.USER, "out_of_stock"),
                                         reply_markup=back_to_main_builder.as_markup())


async def create_message_with_bought_items(bought_data: list):
    message = "<b>"
    for count, item in enumerate(bought_data, start=1):
        private_data = item.private_data
        message += Localizator.get_text(BotEntity.USER, "purchased_item").format(count=count,
                                                                                 private_data=private_data)
    message += "</b>"
    return message


@all_categories_router.callback_query(AllCategoriesCallback.filter(), IsUserExistFilter())
async def navigate_categories(call: CallbackQuery, callback_data: AllCategoriesCallback):
    current_level = callback_data.level

    levels = {
        0: all_categories,
        1: show_subcategories_in_category,
        2: select_quantity,
        3: buy_confirmation,
        4: buy_processing
    }

    current_level_function = levels[current_level]

    await current_level_function(call)
