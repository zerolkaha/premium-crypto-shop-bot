import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.config import BOT_TOKEN
from keyboards import main_menu, catalog_keyboard, product_detail_keyboard
from database import init_db, get_products, add_user, get_product_by_id

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ID администратора (замените на свой Telegram ID)
ADMIN_ID = 1004197981  # ЗАМЕНИТЕ НА ВАШ ID

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# FSM состояния для промокода
class PromoStates(StatesGroup):
    waiting_for_promo = State()


# Словарь для хранения примененных промокодов пользователей
user_promos = {}


# Хэндлер команды /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username)

    welcome_text = (
        "🏆 **PREMIUM DIGITAL SHOP**\n\n"
        "💎 Добро пожаловать в эксклюзивный магазин цифровых товаров!\n\n"
        "Выберите интересующий раздел:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🛍️ Каталог товаров", callback_data="catalog")
    builder.button(text="⭐️ Отзывы", callback_data="reviews")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="⚙️ Админ-панель", callback_data="admin_panel")
    builder.button(text="ℹ️ О нас / Поддержка", callback_data="support")
    builder.adjust(1)

    await message.answer(
        welcome_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )



# Хэндлер для админ-панели
@dp.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery):
    # Проверку полностью удалили! Доступ открыт сразу.
    admin_text = (
        "📊 **СТАТИСТИКА МАГАЗИНА**\n\n"
        "💰 Выручка за месяц: 145,200 ₽\n"
        "📦 Успешных сделок: 290\n"
        "👤 Всего клиентов: 1,840\n"
        "📈 Конверсия: 15.8%\n\n"
        "⚙️ Управление магазином:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Рассылка пользователям", callback_data="admin_broadcast")
    builder.button(text="🏷 Изменить цены", callback_data="admin_prices")
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        admin_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


# Хэндлеры для админских кнопок (заглушки)
@dp.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery):
    """Заглушка для рассылки"""
    await callback.answer("📝 Функция рассылки в разработке", show_alert=True)


@dp.callback_query(F.data == "admin_prices")
async def callback_admin_prices(callback: CallbackQuery):
    """Заглушка для изменения цен"""
    await callback.answer("🏷 Функция изменения цен в разработке", show_alert=True)


# Хэндлер для кнопки "Каталог товаров"
@dp.callback_query(F.data == "catalog")
async def callback_catalog(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку "Каталог товаров".
    Загружает товары из базы данных и отображает их в виде кнопок.
    """
    # Получаем список товаров из базы данных
    products = await get_products()

    if not products:
        await callback.message.edit_text(
            "🛍️ **КАТАЛОГ ТОВАРОВ**\n\n"
            "К сожалению, товары временно отсутствуют.",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    else:
        catalog_text = (
            "💎 **PREMIUM КАТАЛОГ**\n\n"
            "🔥 Эксклюзивные цифровые товары высшего качества\n"
            "⚡️ Моментальная доставка после оплаты\n"
            "🔒 Гарантия безопасности сделки\n\n"
            "Выберите товар:"
        )
        await callback.message.edit_text(
            catalog_text,
            reply_markup=catalog_keyboard(products),
            parse_mode="Markdown"
        )

    await callback.answer()


# Хэндлер для просмотра товара (нажатие на кнопку с товаром)
@dp.callback_query(F.data.startswith("prod_"))
async def callback_product_detail(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку товара.
    Показывает детальную информацию о товаре с кнопками покупки.
    """
    # Извлекаем ID товара из callback_data
    product_id = int(callback.data.split("_")[1])

    # Получаем товар из базы данных
    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return

    product_id, name, description, price_usdt, file_path = product

    # Формируем премиальное сообщение с информацией о товаре
    message_text = (
        f"💎 **{name}**\n\n"
        f"📝 **Описание:**\n{description}\n\n"
        f"💰 **Стоимость:** 500 руб.\n"
        f"⚡️ **Доставка:** Мгновенно\n"
        f"🔒 **Гарантия:** 100%"
    )

    await callback.message.edit_text(
        message_text,
        reply_markup=product_detail_keyboard(product_id),
        parse_mode="Markdown"
    )
    await callback.answer()


# Хэндлер для кнопки "Купить" (выбор способа оплаты)
@dp.callback_query(F.data.startswith("buy_"))
async def callback_buy_product(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку "Купить".
    Показывает выбор способа оплаты.
    """
    # Извлекаем ID товара из callback_data
    product_id = int(callback.data.split("_")[1])

    # Получаем товар из базы данных
    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return

    _, name, description, price_usdt, file_path = product

    # Проверяем, есть ли у пользователя активный промокод
    user_id = callback.from_user.id
    discount = 0
    promo_info = ""

    if user_id in user_promos:
        discount = user_promos[user_id]['discount']
        promo_info = f"\n🎫 Промокод применен! Скидка {discount}%"

    # Рассчитываем финальную цену
    final_price = 500 - (500 * discount // 100)

    # Формируем сообщение оформления заказа
    message_text = (
        f"🛒 **ОФОРМЛЕНИЕ ЗАКАЗА**\n\n"
        f"📦 **Товар:** {name}\n"
        f"💰 **К оплате:** {final_price} руб.{promo_info}\n\n"
        f"Выберите способ оплаты:"
    )

    # Создаем кнопки выбора способа оплаты
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Банковская карта", callback_data=f"pay_card_{product_id}")
    builder.button(text="₿ Криптовалюта", callback_data=f"pay_crypto_{product_id}")
    builder.button(text="🎫 Ввести промокод", callback_data=f"promo_{product_id}")
    builder.button(text="⬅️ Отмена", callback_data=f"prod_{product_id}")
    builder.adjust(1)

    await callback.message.edit_text(
        message_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


# Хэндлер для обработки оплаты (карта или крипта)
@dp.callback_query(F.data.startswith("pay_card_") | F.data.startswith("pay_crypto_"))
async def callback_process_payment(callback: CallbackQuery):
    """
    Обработчик процесса оплаты с имитацией ожидания и подтверждения.
    """
    # Извлекаем ID товара из callback_data
    parts = callback.data.split("_")
    product_id = int(parts[2])

    # Получаем товар из базы данных
    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return

    _, name, description, price_usdt, file_path = product

    # Показываем процесс ожидания транзакции
    await callback.message.edit_text(
        "⏳ Ожидаем подтверждение транзакции..."
    )
    await callback.answer()

    # Имитация обработки платежа
    await asyncio.sleep(3)

    # Успешная оплата - БЕЗ parse_mode чтобы избежать ошибок парсинга
    success_message = (
        f"✅ Платеж подтвержден!\n\n"
        f"🔥 Спасибо за покупку!\n"
        f"📦 Ваш товар: {name}\n\n"
        f"🔗 Ссылка на доступ:\n{file_path}\n\n"
        f"💎 Приятного использования!"
    )

    await callback.message.edit_text(
        success_message,
        reply_markup=main_menu()
    )

    logger.info(
        f"Пользователь {callback.from_user.id} успешно купил товар {product_id} (демо режим)"
    )

    # Очищаем промокод после покупки
    if callback.from_user.id in user_promos:
        del user_promos[callback.from_user.id]


# Хэндлер для кнопки "Ввести промокод"
@dp.callback_query(F.data.startswith("promo_"))
async def callback_promo(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки ввода промокода.
    """
    product_id = int(callback.data.split("_")[1])

    # Сохраняем ID товара в состоянии
    await state.update_data(product_id=product_id)
    await state.set_state(PromoStates.waiting_for_promo)

    await callback.message.edit_text(
        "🎫 **ВВОД ПРОМОКОДА**\n\n"
        "Введите ваш промокод в следующем сообщении:\n\n"
        "💡 Совет: попробуйте **CRYPTO2026**",
        parse_mode="Markdown"
    )
    await callback.answer()


# Хэндлер для получения промокода от пользователя
@dp.message(PromoStates.waiting_for_promo)
async def process_promo_code(message: Message, state: FSMContext):
    """
    Обработчик ввода промокода пользователем.
    """
    promo_code = message.text.strip().upper()
    data = await state.get_data()
    product_id = data.get('product_id')

    # Проверяем промокод
    if promo_code == "CRYPTO2026":
        # Применяем промокод
        user_promos[message.from_user.id] = {
            'code': promo_code,
            'discount': 20
        }

        await message.answer(
            "✅ **Промокод применен!**\n\n"
            "🎉 Скидка 20%\n"
            "💰 Цена снижена до 400 руб.\n\n"
            "Возвращаемся к оформлению заказа...",
            parse_mode="Markdown"
        )

        # Очищаем состояние
        await state.clear()

        # Возвращаем пользователя к оформлению заказа с примененным промокодом
        # Имитируем нажатие на кнопку "Купить"
        product = await get_product_by_id(product_id)
        if product:
            _, name, description, price_usdt, file_path = product

            message_text = (
                f"🛒 **ОФОРМЛЕНИЕ ЗАКАЗА**\n\n"
                f"📦 **Товар:** {name}\n"
                f"💰 **К оплате:** 400 руб.\n"
                f"🎫 Промокод применен! Скидка 20%\n\n"
                f"Выберите способ оплаты:"
            )

            builder = InlineKeyboardBuilder()
            builder.button(text="💳 Банковская карта", callback_data=f"pay_card_{product_id}")
            builder.button(text="₿ Криптовалюта", callback_data=f"pay_crypto_{product_id}")
            builder.button(text="⬅️ Отмена", callback_data=f"prod_{product_id}")
            builder.adjust(1)

            await message.answer(
                message_text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
    else:
        # Добавляем кнопку отмены, чтобы пользователь мог выйти из состояния
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Отмена", callback_data=f"cancel_promo_{product_id}")
        builder.adjust(1)

        await message.answer(
            "❌ **Промокод не найден**\n\n"
            "Проверьте правильность ввода и попробуйте снова.\n\n"
            "💡 Совет: попробуйте **CRYPTO2026**",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        # НЕ очищаем состояние, чтобы пользователь мог попробовать снова


# Хэндлер для отмены ввода промокода
@dp.callback_query(F.data.startswith("cancel_promo_"))
async def callback_cancel_promo(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки отмены ввода промокода.
    Очищает состояние и возвращает на карточку товара.
    """
    product_id = int(callback.data.split("_")[2])

    # Очищаем состояние
    await state.clear()

    # Получаем товар из базы данных
    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return

    _, name, description, price_usdt, file_path = product

    # Возвращаем на карточку товара
    message_text = (
        f"💎 **{name}**\n\n"
        f"📝 **Описание:**\n{description}\n\n"
        f"💰 **Стоимость:** 500 руб.\n"
        f"⚡️ **Доставка:** Мгновенно\n"
        f"🔒 **Гарантия:** 100%"
    )

    await callback.message.edit_text(
        message_text,
        reply_markup=product_detail_keyboard(product_id),
        parse_mode="Markdown"
    )
    await callback.answer()


# Хэндлер для эмуляции успешной оплаты (старый, оставлен для совместимости)
@dp.callback_query(F.data.startswith("test_pay_"))
async def callback_test_payment(callback: CallbackQuery):
    """
    Обработчик эмуляции успешной оплаты.
    Выдает товар пользователю после имитации платежа.
    """
    # Извлекаем ID товара из callback_data
    product_id = int(callback.data.split("_")[2])

    # Получаем товар из базы данных
    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не найден!", show_alert=True)
        return

    _, name, description, price_usdt, file_path = product

    # Отправляем товар пользователю
    success_message = (
        f"🎉 Оплата прошла успешно!\n\n"
        f"Спасибо за покупку '{name}'!\n"
        f"💰 Оплачено: {int(price_usdt) * 100} руб. (тестовый режим)\n\n"
        f"📦 Ваш товар:\n{file_path}\n\n"
        f"Приятного использования!"
    )

    await callback.message.edit_text(
        success_message,
        reply_markup=main_menu()
    )
    await callback.answer("✅ Товар успешно получен!", show_alert=False)

    logger.info(
        f"Пользователь {callback.from_user.id} успешно купил товар {product_id} (тестовый режим)"
    )


# Хэндлер для кнопки "Профиль"
@dp.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку "Профиль".
    """
    profile_text = (
        "👤 **ВАШ ПРОВИЛЬ**\n\n"
        f"🆔 **ID:** `{callback.from_user.id}`\n"
        f"👤 **Имя:** {callback.from_user.full_name}\n"
        f"💰 **Баланс:** 0.00 ⭐️\n\n"
        "⚡️ _Функционал личного кабинета полностью активен_"
    )

    # Создаем чистую инлайн-кнопку возврата вместо всего меню
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        profile_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Хэндлер для кнопки "Отзывы"
# Хэндлер для кнопки "Отзывы"
@dp.callback_query(F.data == "reviews")
async def callback_reviews(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку "Отзывы".
    """
    reviews_text = (
        "⭐️ **ОТЗЫВЫ НАШИХ КЛИЕНТОВ**\n\n"
        "📊 **Средний рейтинг:** 4.9/5.0 ⭐️⭐️⭐️⭐️⭐️\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 **Алексей М.**\n"
        "⭐️⭐️⭐️⭐️⭐️ 5/5\n"
        "\"Отличный магазин! Товар получил моментально после оплаты. Качество на высоте, всё работает как описано. Рекомендую!\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 **Мария К.**\n"
        "⭐️⭐️⭐️⭐️⭐️ 5/5\n"
        "\"Покупала курс по автоматизации - очень довольна! Информация структурированная, всё понятно объяснено. Цена адекватная.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 **Дмитрий В.**\n"
        "⭐️⭐️⭐️⭐️ 4/5\n"
        "\"Хороший сервис, быстрая поддержка. Минус одна звезда только за то, что хотелось бы больше вариантов оплаты.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 **Елена Ш.**\n"
        "⭐️⭐️⭐️⭐️⭐️ 5/5\n"
        "\"Покупаю здесь уже не первый раз. Всегда всё четко и без проблем. Спасибо за качественный продукт! 💎\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    # Создаем аккуратную отдельную кнопку возврата вместо всего меню
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        reviews_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


# Хэндлер для кнопки "О нас / Поддержка"
@dp.callback_query(F.data == "support")
async def callback_support(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку "О нас / Поддержка".
    """
    await callback.answer(
        "ℹ️ Раздел поддержки скоро будет доступен!",
        show_alert=True
    )


# Хэндлер для кнопки "Назад в меню"
@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """
    Обработчик возврата в главное меню.
    """
    await callback.message.edit_text(
        "🏆 **PREMIUM DIGITAL SHOP**\n\n"
        "💎 Добро пожаловать в эксклюзивный магазин цифровых товаров!\n\n"
        "Выберите интересующий раздел:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def main():
    """
    Главная функция для запуска бота.
    Инициализирует базу данных и запускает polling.
    """
    # Инициализируем базу данных при старте бота
    await init_db()
    logger.info("База данных инициализирована")

    logger.info("Бот запущен (тестовый режим оплаты)")
    try:
        # Пропускаем накопившиеся обновления и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    # Запуск бота
    asyncio.run(main())
