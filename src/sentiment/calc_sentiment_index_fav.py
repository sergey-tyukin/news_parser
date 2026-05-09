import sqlite3
import logging
import json
import math
from datetime import datetime, timedelta
from tqdm import tqdm
from src.utils.config_loader import setup_logging, execute_sql_query, PROJECT_ROOT


def calculate_index():
    setup_logging("sentiment.log")
    logger = logging.getLogger(__name__)
    logger.info("=== Начинаем этап определения сентимента в новостях ===")

    conn = sqlite3.connect(PROJECT_ROOT / "data" / "news_fav.sqlite")
    read_cursor = conn.cursor()
    write_cursor = conn.cursor()

    # Получаем дату самой старой новости
    sql_query = 'SELECT MIN(date) FROM news WHERE sentiment_score IS NOT NULL;'
    sql_query_descr = "Получение даты самой старой новости"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)
    first_news_date = read_cursor.fetchone()[0]
    if first_news_date:
        first_news_date = datetime.fromisoformat(first_news_date).date()
    else:
        logger.info("Нет новостей для обработки")
        return
    logger.info(f"Дата самой старой новости: {first_news_date}")

    # Получаем дату самого свежего индекса сентимента (если есть)
    sql_query = 'SELECT MAX(date) FROM sentiment;'
    sql_query_descr = "Получение даты самого последнего индекса сентимента"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)
    last_sentiment_date = read_cursor.fetchone()[0]
    if last_sentiment_date:
        last_sentiment_date = datetime.fromisoformat(last_sentiment_date).date()
        start_day = last_sentiment_date + timedelta(days=1)
    else:
        logger.info('Индекс сентимента ещё не считался, обрабатываем все новости')
        start_day = first_news_date
    end_date = datetime.now().date()
    total_days = (end_date - start_day).days + 1

    logger.info(f"Начинаем определение сентимента с {start_day} до {end_date} (всего {total_days} дней)")

    with tqdm(total=total_days, desc="Вычисление индекса", unit="запись") as pbar:
        current_date = start_day

        # Итерируемся по датам
        while current_date <= end_date:
            start_datetime = datetime.combine(current_date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)

            sql_query = """
                SELECT news.mentioned_companies, sentiment_label.label
                FROM news
                INNER JOIN sentiment_label ON news.sentiment_label_id = sentiment_label.id
                WHERE sentiment_label_id IS NOT NULL AND date >= ? AND date < ?"""
            sql_query_descr = f"Получение списка новостей за {current_date}"
            execute_sql_query(read_cursor, sql_query, sql_query_descr, (start_datetime.isoformat(), end_datetime.isoformat()), logger)
            news = read_cursor.fetchall()

            sentiment = {}

            # Итерируемся по новостям внутри даты
            for item in news:
                sentiment_label = item[1]
                companies = list(json.loads(item[0]))

                # Итерируемся по компаниям внутри новости
                for company in companies:
                    if company not in sentiment:
                        sentiment[company] = {'negative': 0, 'neutral': 0, 'positive': 0}
                    sentiment[company][sentiment_label] += 1

            for ticker, labels_count in sentiment.items():
                rating = math.log((1 + labels_count['positive'])/(1 + labels_count['negative']))

                sql_query_descr = f'Добавление сентимента по "{ticker}" за дату "{current_date}"'
                sql_query = ('''INSERT INTO sentiment (date, ticker, sentiment_score)
                                                 VALUES (?, ?, ?)''')
                execute_sql_query(write_cursor, sql_query, sql_query_descr, (current_date, ticker, rating), logger)

            conn.commit()

            pbar.update(1)
            current_date += timedelta(days=1)

    logger.info("=== Этап определения сентимента в новостях завершен ===")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    calculate_index()
