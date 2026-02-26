import json
import logging
import re
import sqlite3
from tqdm import tqdm
from src.utils.config_loader import setup_logging, execute_sql_query, PROJECT_ROOT, DB_PATH


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

    companies_file = PROJECT_ROOT / "data" / "reference" / "companies.json"

    conn = sqlite3.connect(DB_PATH)
    read_cursor = conn.cursor()
    write_cursor = conn.cursor()

    logger.info("Запуск поиска упоминаний компаний в новостях")

    with open(companies_file, 'r', encoding='utf-8') as f:
        companies =  json.load(f)
    alias_to_canonical = build_alias_to_canonical(companies)
    logger.info(f"Загружено {len(companies)} компаний с общим числом алиасов: {len(alias_to_canonical)}")

    sql_query = """
        SELECT id, text_processed
        FROM news;
    """
    sql_query_descr = "Получение списка новостей"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)

    total_mentions = 0

    for item in tqdm(read_cursor, desc='Обработка новостей') :
        text = item[1]
        mentioned = find_mentioned_companies(text, alias_to_canonical)


        if mentioned and len(mentioned) <= 3:
            sql_query = "UPDATE news SET mentioned_companies = ? WHERE id = ?"
            sql_query_descr = f'Запись обработанной новости с id={item[0]}.'
            execute_sql_query(write_cursor, sql_query, sql_query_descr,
                              (json.dumps(mentioned, ensure_ascii=False), item[0]), logger)

            total_mentions += len(mentioned)

        if item[0] % 1000 == 0:
            conn.commit()
            logger.info(f"Выполнен промежуточный commit, news_id = {item[0]}.")

    logger.info(f"Выполнен финальный commit.")
    conn.commit()
    conn.close()

    logger.info("Этап извлечения компаний завершён.")

if __name__ == "__main__":
    extract_companies()
