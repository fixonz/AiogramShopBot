import grequests
from pathlib import Path

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from config import SUPPORT_LINK
import logging
from bot import dp, main
from multibot import main as main_multibot
from handlers.admin.admin import admin_router
from handlers.user.all_categories import all_categories_router
from handlers.user.my_profile import my_profile_router
from services.user import UserService
from utils.custom_filters import IsUserExistFilter
from utils.localizator import Localizator, BotEntity

logging.basicConfig(level=logging.INFO)
main_router = Router()


@main_router.message(Command(commands=["start", "help"]))
async def start(message: types.message):
    all_categories_button = types.KeyboardButton(text=Localizator.get_text(BotEntity.USER, "all_categories"))
    my_profile_button = types.KeyboardButton(text=Localizator.get_text(BotEntity.USER, "my_profile"))
    faq_button = types.KeyboardButton(text=Localizator.get_text(BotEntity.USER, "faq"))
    help_button = types.KeyboardButton(text=Localizator.get_text(BotEntity.USER, "help"))
    admin_menu_button = types.KeyboardButton(text=Localizator.get_text(BotEntity.ADMIN, "menu"))
    user_telegram_id = message.chat.id
    user_telegram_username = message.from_user.username
    is_exist = await UserService.is_exist(user_telegram_id)
    if is_exist is False:
        await UserService.create(user_telegram_id, user_telegram_username)
    else:
        await UserService.update_receive_messages(user_telegram_id, True)
        await UserService.update_username(user_telegram_id, user_telegram_username)
    keyboard = [[all_categories_button, my_profile_button], [faq_button, help_button]]
    if user_telegram_id in config.ADMIN_ID_LIST:
        keyboard.append([admin_menu_button])
    start_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, keyboard=keyboard)
    await message.answer(Localizator.get_text(BotEntity.COMMON, "start_message"), reply_markup=start_markup)


@main_router.message(F.text == Localizator.get_text(BotEntity.USER, "faq"), IsUserExistFilter())
async def faq(message: types.message):
    await message.answer(Localizator.get_text(BotEntity.USER, "faq_string"))


@main_router.message(F.text == Localizator.get_text(BotEntity.USER, "help"), IsUserExistFilter())
async def support(message: types.message):
    admin_keyboard_builder = InlineKeyboardBuilder()

    admin_keyboard_builder.button(text=Localizator.get_text(BotEntity.USER, "help_button"), url=SUPPORT_LINK)
    await message.answer(Localizator.get_text(BotEntity.USER, "help_string"),
                         reply_markup=admin_keyboard_builder.as_markup())


main_router.include_router(admin_router)
main_router.include_router(my_profile_router)
main_router.include_router(all_categories_router)

if __name__ == '__main__':
    photos_folder = Path("photos")
    if photos_folder.exists() is False:
        photos_folder.mkdir()
    if config.MULTIBOT:
        main_multibot(main_router)
    else:
        dp.include_router(main_router)
        main()
