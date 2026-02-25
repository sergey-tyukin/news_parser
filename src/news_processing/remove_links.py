import re
import json
import logging
import sqlite3

from src.utils.config_loader import setup_logging, PROJECT_ROOT, DB_PATH


def remove_links(news_text):
    url_pattern1 = r'\(\s*https?://[\S]+\s*\)'
    url_pattern2 = r'https?://[\S]+'
    processed_news_text = re.sub(url_pattern1, "(<ссылка>)", news_text)
    processed_news_text = re.sub(url_pattern2, "<ссылка>", processed_news_text)
    return processed_news_text


def main():
    setup_logging('extract_companies.log')
    logger = logging.getLogger(__name__)

    logger.info("Запуск удаления ссылок")

    conn = sqlite3.connect(DB_PATH)
    read_cursor = conn.cursor()
    write_cursor = conn.cursor()

    sql_query = """
        SELECT id, text_original
        FROM news
        WHERE text_processed IS NULL;
    """
    read_cursor.execute(sql_query)

    for item in read_cursor:
        news_text_without_links = remove_links(item[1])

        write_cursor.execute(
            "UPDATE news SET text_processed = ? WHERE id = ?",
            (news_text_without_links, item[0])
        )

        if item[0] % 1000 == 0:

            conn.commit()
            logger.info(f"Выполнен промежуточный commit, news_id = {item[0]}.")

    logger.info(f"Выполнен финальный commit.")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
