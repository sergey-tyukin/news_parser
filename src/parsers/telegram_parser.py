from telethon import TelegramClient, events
import asyncio
import sqlite3
import logging
from src.utils.config_loader import setup_logging, load_secrets, execute_sql_query, PROJECT_ROOT, DB_PATH


async def fetch_telegram_news(secrets, session_file, logger, conn):
    cursor = conn.cursor()

    sql_query = "SELECT id, link, name FROM channels"
    sql_query_descr = "Получение списка каналов"
    execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)

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
        sql_query_descr = f'Получение максимальной новости по каналу {channel[1]}'

        execute_sql_query(cursor, sql_query, sql_query_descr, (), logger)
        result = cursor.fetchone()
        last_id = result[0] if result and result[0] else 0
        if last_id == 0:
            parsing_depth = 20000
        else:
            parsing_depth = 1000

        logger.info(f'Канал {channel[2]} ({channel[1]}): начинаем парсинг, текущий максимальный ID новости {last_id}')

        try:
            entity = await client.get_entity(channel[1])
            messages = await client.get_messages(entity, limit=parsing_depth)

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
                    cursor = execute_sql_query(cursor, sql_query, sql_query_descr, news_item, logger)

                    added += 1

                    if added % 1000 == 0:
                        conn.commit()
                        logger.info(f"Канал {channel[2]} ({channel[1]}): промежуточный commit, добавлено {added} новостей.")

            conn.commit()
            logger.info(f"Канал {channel[2]} ({channel[1]}): найдено {added} новых сообщений.")

        except Exception as e:
            logger.error(f"Ошибка при парсинге {channel}: {e}")

    await client.disconnect()
    return


def run_telegram_parser():
    setup_logging('parser.log')
    logger = logging.getLogger(__name__)

    logger.info('=== Начинаем этап парсинга новостей ===')

    session_file = PROJECT_ROOT / "data" / "sessions" / "telegram_parser"
    secrets = load_secrets()

    conn = sqlite3.connect(DB_PATH)

    asyncio.run(fetch_telegram_news(
        secrets=secrets,
        session_file=session_file,
        logger=logger,
        conn=conn
    ))

    logger.info('=== Этап парсинга новостей завершен ===')


if __name__ == '__main__':
    run_telegram_parser()
