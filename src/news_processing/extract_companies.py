import json
import logging

from src.utils.config_loader import setup_logging, PROJECT_ROOT


def build_alias_to_canonical(companies_dict):
    """Создаёт маппинг: alias (в нижнем регистре) → каноническое имя."""
    alias_to_canonical = {}
    for canonical, aliases in companies_dict.items():
        for alias in aliases:
            alias_to_canonical[alias.lower()] = canonical
    return alias_to_canonical


def find_mentioned_companies(text: str, alias_to_canonical: dict) -> list:
    if not text:
        return []
    text_lower = text.lower()
    mentioned = set()
    for alias, canonical in alias_to_canonical.items():
        if alias in text_lower:
            mentioned.add(canonical)
    return list(mentioned)


def extract_companies():
    setup_logging('extract_companies.log')
    logger = logging.getLogger(__name__)

    input_file = PROJECT_ROOT / "data" / "raw" / "news.json"
    companies_file = PROJECT_ROOT / "data" / "reference" / "companies.json"
    output_file = PROJECT_ROOT / "data" / "processed" / "news_with_companies.json"

    logger.info("Запуск извлечения упоминаний компаний из новостей")

    with open(input_file, 'r', encoding='utf-8') as f:
        news =  json.load(f)
    with open(companies_file, 'r', encoding='utf-8') as f:
        companies =  json.load(f)

    alias_to_canonical = build_alias_to_canonical(companies)
    logger.info(f"Загружено {len(companies)} компаний с общим числом алиасов: {len(alias_to_canonical)}")

    total_mentions = 0
    for item in news:
        text = item.get("text", "")
        mentioned = find_mentioned_companies(text, alias_to_canonical)
        item["mentioned_companies"] = mentioned
        total_mentions += len(mentioned)

    logger.info(f"Обработано {len(news)} новостей. Найдено {total_mentions} упоминаний компаний.")


    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные успешно сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении {output_file}: {e}")
        raise

    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(news, f, ensure_ascii=False, indent=2)

    logger.info(f"Данные успешно сохранены в {output_file}")

    logger.info("Этап извлечения компаний завершён.")


if __name__ == "__main__":
    extract_companies()
