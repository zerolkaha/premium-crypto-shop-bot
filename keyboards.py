from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍️ Каталог товаров", callback_data="catalog")
    builder.button(text="⭐️ Отзывы", callback_data="reviews")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="⚙️ Админ-панель", callback_data="admin_panel") # Добавь эту строку
    builder.button(text="ℹ️ О нас / Поддержка", callback_data="support")
    builder.adjust(1)
    return builder.as_markup()


def catalog_keyboard(products: list) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру каталога товаров.

    Args:
        products: Список товаров из базы данных [(id, name, description, price_usdt, file_path), ...]

    Returns:
        InlineKeyboardMarkup: Клавиатура с товарами и кнопкой "Назад"
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопку для каждого товара
    for product in products:
        product_id, name, description, price_usdt, file_path = product
        # Формируем текст кнопки: название товара + цена в звёздах
        button_text = f"{name} — {int(price_usdt)} ⭐️"
        # callback_data содержит ID товара для дальнейшей обработки
        builder.button(text=button_text, callback_data=f"prod_{product_id}")

    # Добавляем кнопку "Назад в меню"
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")

    # По одной кнопке в ряд
    builder.adjust(1)

    return builder.as_markup()


def product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для страницы товара с кнопками покупки и возврата.

    Args:
        product_id: ID товара

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками "Купить" и "Назад"
    """
    builder = InlineKeyboardBuilder()

    builder.button(text="💳 Перейти к оплате", callback_data=f"buy_{product_id}")
    builder.button(text="⬅️ Назад в каталог", callback_data="catalog")

    builder.adjust(1)

    return builder.as_markup()


# payment_keyboard больше не используется (удалена логика Crypto Pay)
