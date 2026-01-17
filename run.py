from src.parsers import telegram_parser
from src.news_processing import remove_links, extract_companies
from src.sentiment import sentiment

telegram_parser.run_telegram_parser()
remove_links.remove_links()
extract_companies.extract_companies()
sentiment.get_sentiment()
