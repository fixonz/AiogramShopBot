import logging
from typing import Union
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.subcategory import SubcategoryService
from services.category import CategoryService
from services.user import UserService
from config import ADMIN_ID_LIST
from models.user import User
from utils.localizator import Localizator, BotEntity
from utils.other_sql import RefundBuyDTO


class NotificationManager:
    @staticmethod
    async def send_refund_message(refund_data: RefundBuyDTO, bot):
        message = Localizator.get_text(BotEntity.USER, "refund_notification").format(
            total_price=refund_data.total_price,
            quantity=refund_data.quantity,
            subcategory=refund_data.subcategory,
            currency_sym=Localizator.get_currency_symbol())
        try:
            await bot.send_message(refund_data.telegram_id, f"<b>{message}</b>")
        except Exception as e:
            logging.error(e)

    @staticmethod
    async def send_to_admins(message: str, reply_markup: types.InlineKeyboardMarkup, bot):
        for admin_id in ADMIN_ID_LIST:
            try:
                await bot.send_message(admin_id, f"<b>{message}</b>", reply_markup=reply_markup)
            except Exception as e:
                logging.error(e)

    @staticmethod
    async def make_user_button(username: Union[str, None]):
        user_button_builder = InlineKeyboardBuilder()
        if isinstance(username, str):
            user_button_inline = types.InlineKeyboardButton(text=username, url=f"https://t.me/{username}")
            user_button_builder.add(user_button_inline)
        return user_button_builder.as_markup()

    @staticmethod
    async def new_deposit(new_crypto_balances: dict, deposit_amount_usd, telegram_id: int, bot):
        deposit_amount_usd = round(deposit_amount_usd, 2)
        merged_crypto_balances = {
            key.replace('_deposit', "").replace('_', ' ').upper(): value
            for key, value in new_crypto_balances.items()
        }

        user = await UserService.get_by_tgid(telegram_id)
        user_button = await NotificationManager.make_user_button(user.telegram_username)
        address_map = {
            "LTC": user.ltc_address
        }
        crypto_key = list(merged_crypto_balances.keys())[0]
        addr = next((address_map[key] for key in address_map if key in crypto_key), "")
        if user.telegram_username:
            user_identifier = user.telegram_username
            message_template = "notification_new_deposit_username"
        else:
            user_identifier = telegram_id
            message_template = "notification_new_deposit_id"

        message = Localizator.get_text(BotEntity.ADMIN, message_template).format(
            username=user_identifier,
            deposit_amount_fiat=deposit_amount_usd,
            currency_sym=Localizator.get_currency_symbol()
        )
        for crypto_name, value in merged_crypto_balances.items():
            if value > 0:
                message += Localizator.get_text(BotEntity.ADMIN, "notification_crypto_deposit").format(
                    value=value,
                    crypto_name=crypto_name,
                    crypto_address=addr
                )
        message += Localizator.get_text(BotEntity.ADMIN, "notification_seed").format(seed=user.seed)
        await NotificationManager.send_to_admins(message, user_button, bot)

    @staticmethod
    async def new_buy(category_id: int, subcategory_id: int, quantity: int, total_price: float, user: User, bot):
        subcategory = await SubcategoryService.get_by_primary_key(subcategory_id)
        category = await CategoryService.get_by_primary_key(category_id)
        message = ""
        username = user.telegram_username
        telegram_id = user.telegram_id
        user_button = await NotificationManager.make_user_button(username)
        if username:
            message += Localizator.get_text(BotEntity.ADMIN, "notification_purchase_with_tgid").format(
                username=username,
                total_price=total_price,
                quantity=quantity,
                subcategory_name=subcategory.name,
                category_name=category.name,
                currency_sym=Localizator.get_currency_symbol())
        else:
            message += Localizator.get_text(BotEntity.ADMIN, "notification_purchase_with_username").format(
                telegram_id=telegram_id,
                total_price=total_price,
                quantity=quantity,
                subcategory_name=subcategory.name,
                category_name=category.name,
                currency_sym=Localizator.get_currency_symbol())
        await NotificationManager.send_to_admins(message, user_button, bot)
