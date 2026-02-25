import sqlite3
import logging
import yaml
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel
from src.utils.config_loader import setup_logging, PROJECT_ROOT, load_secrets, DB_PATH


async def get_channel_title(secrets, session_file, link):

    async with TelegramClient(session_file, secrets['telegram']['api_id'], secrets['telegram']['api_hash']) as client:
        try:
            entity = await client.get_entity(link)
            if isinstance(entity, Channel):
                return entity.title
            else:
                return f"Ошибка, {link} - это не канал, а {type(entity).__name__}"
        except Exception as e:
            return f"Ошибка: {str(e)}"


def execute_sql_query(cursor, sql_query, sql_query_descr, sql_query_params, logger):
    try:
        cursor.execute(sql_query, sql_query_params)
        logger.info(f'Выполнен запрос: {sql_query_descr}')
    except sqlite3.Error as e:
        logger.info(f'Запрос {sql_query_descr} не выполнен. Ошибка: {e}')

def main():
    setup_logging('db_create.log')
    logger = logging.getLogger(__name__)

    secrets = load_secrets()

    session_file = PROJECT_ROOT / "data" / "sessions" / "telegram_parser"
    channels_file = PROJECT_ROOT / "config" / "telegram_channels.yaml"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(channels_file, 'r', encoding='utf-8') as f:
        channels = [url.strip() for url in yaml.safe_load(f) if isinstance(url, str)]

    for channel in channels:
        title = asyncio.run(get_channel_title(secrets, session_file, channel))
        new_channel = (channel, title)

        sql_query_descr = f'Добавление канала "{title}", ссылка: "{channel}"'
        sql_query = 'INSERT INTO channels (link, name) VALUES (?, ?)'
        execute_sql_query(cursor, sql_query, sql_query_descr, new_channel, logger)
        conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
