import re
import json
import logging

from src.utils.config_loader import setup_logging, PROJECT_ROOT


def remove_links():
    setup_logging('extract_companies.log')
    logger = logging.getLogger(__name__)

    input_file = PROJECT_ROOT / "data" / "raw" / "news.json"
    output_file = PROJECT_ROOT / "data" / "processed" / "news_without_links.json"

    logger.info("Запуск удаления ссылок")

    with open(input_file, 'r', encoding='utf-8') as f:
        news =  json.load(f)

    url_pattern1 = r'\(\s*https?://[\S]+\s*\)'
    url_pattern2 = r'https?://[\S]+'

    for item in news:
        item["text"] = re.sub(url_pattern1, "(<ссылка>)", item["text"])
        item["text"] = re.sub(url_pattern2, "<ссылка>", item["text"])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные успешно сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении {output_file}: {e}")
        raise

if __name__ == "__main__":
    remove_links()
