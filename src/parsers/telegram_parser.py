from telethon import TelegramClient, events
import asyncio
import json
import logging

from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT


CHANNELS = [
    'https://t.me/AK47pfl',
    'https://t.me/finpizdec',
]

OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "news.json"
SESSION_FILE = PROJECT_ROOT / "data" / "sessions" / "telegram_parser"

setup_logging('parser.log')
logger = logging.getLogger(__name__)

secrets = load_secrets()

async def main():
    client = TelegramClient(SESSION_FILE, secrets["telegram"]["api_id"], secrets["telegram"]["api_hash"])

    await client.start(phone=secrets["telegram"]["phone"])
    logger.info("Клиент для парсинга новостей из Telegram запущен!")

    # Загружаем существующие новости, чтобы определить последний ID по каждому каналу
    existing_news = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing_news = json.load(f)

    # Собираем последние ID
    last_ids = {}
    for item in existing_news:
        channel = item['channel']
        msg_id = item['message_id']
        if channel not in last_ids or msg_id > last_ids[channel]:
            last_ids[channel] = msg_id

    news = []

    for channel in CHANNELS:
        try:
            entity = await client.get_entity(channel)
            messages = await client.get_messages(entity, limit=50)

            channel_title = entity.title
            last_id = last_ids.get(channel_title, 0)

            added = 0

            for msg in messages:
                if msg.id <= last_id:
                    break
                if msg.text.strip():
                    news_item = {
                        'channel': entity.title,
                        'message_id': msg.id,
                        'text': msg.text,
                        'date': msg.date.isoformat(),
                        'link': f'https://t.me/{entity.username}/{msg.id}'
                    }
                    news.append(news_item)
                    added += 1
            logger.info(f"Найдено {added} новых сообщений в {channel_title}")

        except Exception as e:
            logger.error(f"Ошибка при парсинге {channel}: {e}")

    all_news = existing_news + news

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    if len(news) > 0:
        logger.info(f"Сохранено {len(news)} новостей в {OUTPUT_FILE} из канала {channel}")

    await client.disconnect()

def run_telegram_parser():
    asyncio.run(main())

if __name__ == '__main__':
    run_telegram_parser()
