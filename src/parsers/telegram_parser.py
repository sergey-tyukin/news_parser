from telethon import TelegramClient, events
import asyncio
import sqlite3
import logging
from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT, DB_PATH


def execute_sql_query(cursor, sql_query, sql_query_descr, sql_query_params, logger):
    try:
        cursor.execute(sql_query, sql_query_params)
        logger.info(f'Выполнен запрос: {sql_query_descr}')
    except sqlite3.Error as e:
        logger.info(f'Запрос {sql_query_descr} не выполнен. Ошибка: {e}')


async def fetch_telegram_news(secrets, session_file, logger, conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id, link, name FROM channels")
    channels = cursor.fetchall()

    client = TelegramClient(session_file, secrets["telegram"]["api_id"], secrets["telegram"]["api_hash"])

    await client.start(phone=secrets["telegram"]["phone"])
    logger.info("Клиент для парсинга новостей из Telegram запущен!")

    for channel in channels:

        sql_query = f'''
            SELECT MAX(message_id) FROM news
            INNER  JOIN channels ON news.channel_id = channels.id
            WHERE channels.id = {channel[0]};
        '''
        cursor.execute(sql_query)
        result = cursor.fetchone()
        last_id = result[0] if result and result[0] else 0

        try:
            entity = await client.get_entity(channel[1])
            messages = await client.get_messages(entity, limit=100)

            channel_title = entity.title

            added = 0

            for msg in messages:
                if msg.id <= last_id:
                    break
                if msg.text is not None and msg.text.strip():
                    news_item = {
                        'channel_id': channel[0],
                        'message_id': msg.id,
                        'text_original': msg.text,
                        'date': msg.date.isoformat(),
                        'link': f'https://t.me/{entity.username}/{msg.id}'
                    }

                    sql_query_descr = f'Парсинг и добавление новости "{msg.id}" с канала "{channel[1]}"'
                    sql_query = ('''INSERT INTO news (channel_id, message_id, text_original, date, link)
                                 VALUES (:channel_id, :message_id, :text_original, :date, :link)''')
                    execute_sql_query(cursor, sql_query, sql_query_descr, news_item, logger)
                    conn.commit()

                    added += 1
            logger.info(f"Найдено {added} новых сообщений в канале {channel[2]} ({channel[1]}).")

        except Exception as e:
            logger.error(f"Ошибка при парсинге {channel}: {e}")

    await client.disconnect()
    return


def run_telegram_parser():
    setup_logging('parser.log')
    logger = logging.getLogger(__name__)

    session_file = PROJECT_ROOT / "data" / "sessions" / "telegram_parser"
    secrets = load_secrets()

    conn = sqlite3.connect(DB_PATH)

    asyncio.run(fetch_telegram_news(
        secrets=secrets,
        session_file=session_file,
        logger=logger,
        conn=conn
    ))


if __name__ == '__main__':
    run_telegram_parser()
