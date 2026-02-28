import sqlite3
import logging
import pandas as pd

from src.utils.config_loader import setup_logging, execute_sql_query, DB_PATH, PROJECT_ROOT


def run_export():
    setup_logging("export_sentiment.log")
    logger = logging.getLogger(__name__)
    logger.info("=== Начинаем этап экспорта сентимента ===")

    output_file_parquet = PROJECT_ROOT / "data" / "processed" / "sentiment.parquet"
    output_file_excel = PROJECT_ROOT / "data" / "processed" / "sentiment.xlsx"
    output_file_csv = PROJECT_ROOT / "data" / "processed" / "sentiment.csv"

    conn = sqlite3.connect(DB_PATH)
    read_cursor = conn.cursor()

    sql_query = 'SELECT date, ticker, sentiment_score FROM sentiment;'
    sql_query_descr = "Выгрузка всех значений сентимента"
    execute_sql_query(read_cursor, sql_query, sql_query_descr, (), logger)

    sentiment = read_cursor.fetchall()
    conn.close()

    sentiment_df = pd.DataFrame(sentiment, columns=['date', 'ticker', 'value'])
    sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])

    sentiment_df.to_parquet(output_file_parquet, index=False)
    logger.info(f"Данные сохранены в {output_file_parquet}")

    sentiment_wide_df = sentiment_df.pivot_table(
        index='date',
        columns='ticker',
        values='value'
    )

    sentiment_wide_df = sentiment_wide_df.sort_index(axis=0).sort_index(axis=1)

    sentiment_wide_df.to_excel(output_file_excel)
    sentiment_wide_df.to_csv(output_file_csv)
    logger.info(f"Данные сохранены в {output_file_excel} и {output_file_csv}")
    logger.info("=== Этап экспорта сентимента завершен ===")


if __name__ == '__main__':
    run_export()
