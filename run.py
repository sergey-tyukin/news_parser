from pathlib import Path
from src.utils.config_loader import DB_PATH
from src.utils import create_db, insert_channels_into_db
from src.parsers import telegram_parser
from src.news_processing import cleaners, extract_companies
from src.sentiment import calc_news_sentiment, calc_sentiment_index

# Создаём базу, если её нет
if not Path(DB_PATH).is_file():
    create_db.create_db()
    insert_channels_into_db.insert_channels()

# Парсим свежие новости
telegram_parser.run_telegram_parser()

# Подготоваливаем новости
cleaners.run_news_cleaner()

# Ищем названия компаний в новостях
extract_companies.extract_companies()

# Определяем сентимент новостей
calc_news_sentiment.get_sentiment()

# Считаем индекс сентимента
calc_sentiment_index.calculate_index()
