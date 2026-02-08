import json
import logging
import re
from tqdm import tqdm
from src.utils.config_loader import setup_logging, PROJECT_ROOT


def build_alias_to_canonical(companies_dict):
    """Создаём маппинг: alias - каноническое имя."""
    alias_to_canonical = {}
    for canonical, aliases in companies_dict.items():
        for alias in aliases['searchnames']:
            alias_to_canonical[alias] = canonical
    return alias_to_canonical


def find_mentioned_companies(text: str, alias_to_canonical: dict) -> list:
    if not text:
        return []
    mentioned = {}

    for alias, canonical in alias_to_canonical.items():
        escaped_alias = re.escape(alias)
        pattern = r'(?:^|\W)' + escaped_alias
        if re.search(pattern, text, re.IGNORECASE):
            if canonical in mentioned:
                mentioned[canonical].append(alias)
            else:
                mentioned[canonical] = [alias]
    return mentioned


def extract_companies():
    setup_logging('extract_companies.log')
    logger = logging.getLogger(__name__)

    input_file = PROJECT_ROOT / "data" / "processed" / "news_without_links.json"
    output_file = PROJECT_ROOT / "data" / "processed" / "news_with_companies.json"
    companies_file = PROJECT_ROOT / "data" / "reference" / "companies.json"

    logger.info("Запуск извлечения упоминаний компаний из новостей")

    with open(input_file, 'r', encoding='utf-8') as f:
        news =  json.load(f)
    with open(companies_file, 'r', encoding='utf-8') as f:
        companies =  json.load(f)

    alias_to_canonical = build_alias_to_canonical(companies)
    print(alias_to_canonical)
    logger.info(f"Загружено {len(companies)} компаний с общим числом алиасов: {len(alias_to_canonical)}")
    logger.info(f"Загружено {len(news)} новостей")

    news_with_companies = []
    total_mentions = 0

    for item in tqdm(news, desc='Обработка новостей'):
        text = item.get("text", "")
        mentioned = find_mentioned_companies(text, alias_to_canonical)
        if mentioned and len(mentioned) <= 3:
            item["mentioned_companies"] = mentioned
            news_with_companies.append(item)
            total_mentions += len(mentioned)

    logger.info(f"Обработано {len(news)} новостей. Найдено {total_mentions} упоминаний компаний в {len(news_with_companies)} новостях.")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_with_companies, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные успешно сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении {output_file}: {e}")
        raise

    logger.info("Этап извлечения компаний завершён.")

if __name__ == "__main__":
    extract_companies()
