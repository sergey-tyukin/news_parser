from src.parsers import telegram_parser
from src.news_processing import cleaners, extract_companies
from src.sentiment import sentiment

# Парсим свежие новости
telegram_parser.run_telegram_parser()

# Подготоваливаем новости
cleaners.run_news_cleaner()


# extract_companies.extract_companies()
# sentiment.get_sentiment()
