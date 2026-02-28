import sqlite3
import logging
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

from src.utils.config_loader import setup_logging, execute_sql_query, PROJECT_ROOT, DB_PATH


def get_sentiment():
    setup_logging("sentiment.log")
    logger = logging.getLogger(__name__)
    logger.info("=== Начинаем этап определения сентимента в новостях ===")

    conn = sqlite3.connect(DB_PATH)
    read_cursor = conn.cursor()
    write_cursor = conn.cursor()

    sql_query = "SELECT id, label FROM sentiment_label;"
    sql_query_descr = "Загружаем метки сентимента"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)
    labels = read_cursor.fetchall()
    labels = {name: key for key, name in labels}

    sql_query = 'SELECT COUNT(*) FROM news WHERE for_processing = 1'
    sql_query_descr = "Получение количества новостей"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)
    news_count = read_cursor.fetchone()[0]
    logger.info(f"В базе находится {news_count} новостей для обработки")

    sql_query = "SELECT id, text_processed FROM news WHERE for_processing = 1;"
    sql_query_descr = "Получение списка новостей"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)

    model_name = PROJECT_ROOT / "src" / "sentiment" / ".rubert-tiny2-russian-financial-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    classifier = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        device=-1,  # явно указываем, что считаем на CPU
        truncation = True,
        max_length = 2040
    )

    for item in tqdm(read_cursor, desc='Обработка новостей') :
        text = item[1]

        try:
            result = classifier(text)[0]
        except Exception as e:
            logger.error(f"Ошибка при определении сентимента у новости {item}: {e}")
            continue

        sql_query = """UPDATE news
            SET sentiment_label_id = ?, sentiment_score = ?, for_processing = ?
            WHERE id = ?"""
        sql_query_descr = f'Запись компаний для новости с id={item[0]}'
        execute_sql_query(write_cursor, sql_query, sql_query_descr,
                          (labels[result["label"]], round(result["score"], 4), 0, item[0]), logger)

    logger.info("=== Этап определения сентимента в новостях завершен ===")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    get_sentiment()
