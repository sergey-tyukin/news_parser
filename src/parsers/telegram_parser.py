from telethon import TelegramClient, events
import asyncio
import json
import yaml
import logging


from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT


async def fetch_telegram_news(secrets, session_file, channels, last_ids, logger):
    client = TelegramClient(session_file, secrets["telegram"]["api_id"], secrets["telegram"]["api_hash"])

    await client.start(phone=secrets["telegram"]["phone"])
    logger.info("Клиент для парсинга новостей из Telegram запущен!")

    news = []

    for channel in channels:
        try:
            entity = await client.get_entity(channel)
            messages = await client.get_messages(entity, limit=50)

            channel_title = entity.title
            last_id = last_ids.get(channel_title, 0)

            added = 0

            for msg in messages:
                if msg.id <= last_id:
                    break
                if msg.text is not None and msg.text.strip():
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

    await client.disconnect()
    return news


def run_telegram_parser():
    setup_logging('parser.log')
    logger = logging.getLogger(__name__)

    input_file = PROJECT_ROOT / "config" / "telegram_channels.yaml"
    output_file = PROJECT_ROOT / "data" / "raw" / "news.json"
    session_file = PROJECT_ROOT / "data" / "sessions" / "telegram_parser"
    secrets = load_secrets()

    with open(input_file, 'r', encoding='utf-8') as f:
        channels = [url.strip() for url in yaml.safe_load(f) if isinstance(url, str)]

    # Загружаем существующие новости, чтобы определить последний ID по каждому каналу
    existing_news = []
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_news = json.load(f)

    # Собираем последние ID
    last_ids = {}
    for item in existing_news:
        channel = item['channel']
        msg_id = item['message_id']
        if channel not in last_ids or msg_id > last_ids[channel]:
            last_ids[channel] = msg_id

    news = asyncio.run(fetch_telegram_news(
        secrets=secrets,
        session_file=session_file,
        channels=channels,
        last_ids=last_ids,
        logger=logger
    ))

    if len(news) > 0:
        all_news = existing_news + news

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)

        logger.info(f"Сохранено {len(news)} новостей из {len(channels)} в {output_file}")
    else:
        logger.info(f"Файл {output_file} оставлен без изменений")


if __name__ == '__main__':
    run_telegram_parser()
