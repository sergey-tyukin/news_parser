import sqlite3
import logging
from src.utils.config_loader import setup_logging, execute_sql_query, DB_PATH


def create_db():
    setup_logging('db_create.log')
    logger = logging.getLogger(__name__)

    logger.info('=== Начинаем этап создания базы данных ===')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    sql_query_descr = 'Включение поддержки внешних ключей'
    sql_query = 'PRAGMA foreign_keys = ON;'
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = 'Создание таблицы channels'
    sql_query = '''
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY,
        link TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    );
    '''

    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = 'Создание таблицы sentiment_label'
    sql_query = '''
    CREATE TABLE IF NOT EXISTS sentiment_label (
        id INTEGER PRIMARY KEY,
        label TEXT NOT NULL UNIQUE
    );
    '''
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = 'Создание таблицы news'
    sql_query = '''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY,
        channel_id INTEGER NOT NULL REFERENCES channels(id),
        message_id INTEGER NOT NULL,
        text_original TEXT NOT NULL,
        text_processed TEXT,
        date DATETIME NOT NULL,
        link TEXT,
        mentioned_companies TEXT,
        sentiment_label_id INTEGER REFERENCES sentiment_label(id),
        sentiment_score REAL CHECK(sentiment_score BETWEEN -1 AND 1),
        for_processing BOOLEAN NOT NULL DEFAULT 1,
        UNIQUE(channel_id, message_id)
    );
    '''
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = 'Создание индекса для выборки новостей по каналу и дате'
    sql_query = 'CREATE INDEX IF NOT EXISTS idx_news_channel_date ON news(channel_id, date);'
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = 'Создание индекса для агрегации по тональности'
    sql_query = 'CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news(sentiment_label_id);'
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = 'Создание индекса для поиска новости по каналу и ID сообщения'
    sql_query = 'CREATE UNIQUE INDEX IF NOT EXISTS idx_news_message ON news(channel_id, message_id);'
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

    sql_query_descr = f'Добавляем значения меток сентимента в таблицу sentiment_label'
    sql_query = '''INSERT INTO sentiment_label (label) VALUES (?)'''
    for label in ['negative', 'neutral', 'positive']:
        execute_sql_query(cursor, sql_query, sql_query_descr, (label, ), logger)

    conn.commit()
    conn.close()

    logger.info('=== Этап создания базы данных завершен ===')


if __name__ == "__main__":
    create_db()
