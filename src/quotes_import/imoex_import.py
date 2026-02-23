from moexalgo import Ticker, session
from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT


# output_file = PROJECT_ROOT / "data" / "raw" / "imoex_quotes_raw.parquet"
output_file = PROJECT_ROOT / "data" / "raw" / "moexbmi_quotes_raw.parquet"

secrets = load_secrets()

session.TOKEN = secrets['moex_alogpack']
# imoex = Ticker('IMOEX')
imoex = Ticker('MOEXBMI')

start_date = '2019-01-01'
end_date = '2026-02-28'

imoex_quotes = imoex.candles(
    start=start_date,
    end=end_date,
    period='1d'
)


if not imoex_quotes.empty:
    price_start = imoex_quotes.iloc[0]['close']
    price_end = imoex_quotes.iloc[-1]['close']


    print(f"Период: {start_date} — {end_date}")
    print(f"Начальная цена: {price_start:.2f}")
    print(f"Конечная цена: {price_end:.2f}")
    print(imoex_quotes)
    for col in imoex_quotes.columns:
        print(f"  • {col}")

    imoex_quotes.to_parquet(output_file, engine="pyarrow")
else:
    print("Нет данных за указанный период")
