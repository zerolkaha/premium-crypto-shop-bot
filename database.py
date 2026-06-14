import aiosqlite
import os


# Путь к файлу базы данных
DB_PATH = os.path.join(os.path.dirname(__file__), 'shop.db')


async def init_db():
    """
    Инициализирует базу данных, создает необходимые таблицы
    и добавляет тестовые товары при первом запуске.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаем таблицу пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT
            )
        """)

        # Создаем таблицу товаров
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price_usdt REAL NOT NULL,
                file_path TEXT
            )
        """)

        await db.commit()

        # Проверяем, есть ли товары в базе
        cursor = await db.execute("SELECT COUNT(*) FROM products")
        count = await cursor.fetchone()

        # Если товаров нет, добавляем тестовые
        if count[0] == 0:
            await add_test_products(db)
            print("✅ Тестовые товары добавлены в базу данных")


async def add_test_products(db: aiosqlite.Connection):
    """
    Добавляет тестовые товары в базу данных.

    Args:
        db: Подключение к базе данных
    """
    test_products = [
        ("Тестовый гайд по крипте", "Подробный гайд для новичков в криптовалютах", 5.0, "files/crypto_guide.txt"),
        ("Курс по автоматизации", "Полный курс по автоматизации процессов с Python", 12.0, "files/automation_course.txt"),
        ("Чек-лист трейдера", "Полезный чек-лист для успешной торговли", 15.0, "files/trader_checklist.txt"),
    ]

    await db.executemany(
        "INSERT INTO products (name, description, price_usdt, file_path) VALUES (?, ?, ?, ?)",
        test_products
    )
    await db.commit()


async def get_products():
    """
    Получает список всех товаров из базы данных.

    Returns:
        list[tuple]: Список кортежей с данными товаров (id, name, description, price_usdt, file_path)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, price_usdt, file_path FROM products"
        )
        products = await cursor.fetchall()
        return products


async def get_product_by_id(product_id: int):
    """
    Получает товар по его ID.

    Args:
        product_id: ID товара

    Returns:
        tuple | None: Данные товара (id, name, description, price_usdt, file_path) или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, price_usdt, file_path FROM products WHERE id = ?",
            (product_id,)
        )
        product = await cursor.fetchone()
        return product


async def add_user(telegram_id: int, username: str = None):
    """
    Добавляет пользователя в базу данных (если его еще нет).

    Args:
        telegram_id: Telegram ID пользователя
        username: Username пользователя (опционально)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
                (telegram_id, username)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            # Пользователь уже существует
            pass
