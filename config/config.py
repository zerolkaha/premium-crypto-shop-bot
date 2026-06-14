import os
from pathlib import Path
from dotenv import load_dotenv

# Определяем путь к корневой директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные окружения из .env файла
env_path = BASE_DIR / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Получаем токены из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CRYPTO_TOKEN = os.getenv('CRYPTO_TOKEN')

# Проверяем, что токены загружены
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")
if not CRYPTO_TOKEN:
    raise ValueError("CRYPTO_TOKEN не найден в .env файле")
