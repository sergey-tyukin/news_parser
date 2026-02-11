import pandas as pd
import logging
import json
from datetime import datetime
from calendar import monthrange
from moexalgo import session, Market, Ticker
from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT


def get_spread(secrets, ticker, start_date, end_date):
    DATE_FORMAT = "%Y-%m-%d"
    session.TOKEN = secrets['moex_alogpack']
    stock = Ticker(ticker)
    current_date = start_date
    dfs = []

    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = month_start.replace(
            day=monthrange(current_date.year, current_date.month)[1]
        )

        interval_start = max(current_date, start_date)
        interval_end = min(month_end, end_date)

        obstats = stock.obstats(
            start=interval_start.strftime(DATE_FORMAT),
            end=interval_end.strftime(DATE_FORMAT)
        )
        dfs.append(pd.DataFrame(obstats))

        if month_end.month == 12:
            current_date = month_end.replace(year=month_end.year + 1, month=1, day=1)
        else:
            current_date = month_end.replace(month=month_end.month + 1, day=1)

        # подчищаем полностью пустые столбцы, чтобы корректно работал pd.concat
        dfs_cleaned = [df.dropna(axis=1, how='all') for df in dfs if not df.empty]
        result = pd.concat(dfs_cleaned, ignore_index=True) if dfs_cleaned else pd.DataFrame()

        if not result.empty:
            result = result.rename(columns={'tradedate': 'date'})
            result['date'] = pd.to_datetime(result['date']).dt.date
            result['tradetime'] = pd.to_timedelta(result['tradetime'])

    return result


if __name__ == "__main__":
    setup_logging('import.log')
    logger = logging.getLogger(__name__)

    companies_file = PROJECT_ROOT / "data" / "raw" / "companies_raw.json"

    with open(companies_file, 'r', encoding='utf-8') as f:
        companies = list(json.load(f).keys())

    secrets = load_secrets()

    start_date = datetime(2020, 1, 1)  # данные хранятся только с 2020 года
    end_date = datetime(2026, 2, 28)

    for ticker in companies:

        spread = get_spread(secrets, ticker, start_date, end_date)

        output_dir = PROJECT_ROOT / "data" / "processed" / "daily_spread"
        output_dir_main = PROJECT_ROOT / "data" / "processed" / "daily_spread_main"

        # Весь день
        spread_daily = spread.groupby('date', as_index=False).median(numeric_only=True)
        spread_daily.to_parquet(output_dir / f'{ticker}.parquet', engine="pyarrow")
        spread_daily.to_excel(output_dir / f'{ticker}.xlsx', index=False)

        # Основная торговая сессия
        spread_daily_main = spread[
            (spread['tradetime'] >= pd.Timedelta('10:05:00')) &
            (spread['tradetime'] <= pd.Timedelta('18:40:00'))
            ]

        spread_daily_main = spread_daily_main.groupby('date', as_index=False).median(numeric_only=True)
        spread_daily.to_parquet(output_dir / f'{ticker}.parquet', engine="pyarrow")
        spread_daily_main.to_excel(output_dir_main / f'{ticker}.xlsx', index=False)
