# Скрипт для первоначальной генерации справочника компаний из данных, получаемых по API
# После генерации файл data/reference/companies_raw.json может редактироваться вручную.
import pandas as pd
import logging
import http.client
import json
import re
from moexalgo import session, Market, Ticker
from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT


def extract_canonical_name(full_name):
    """Извлекаем текст из двойных кавычек (если они есть)"""
    if not isinstance(full_name, str):
        return str(full_name).strip()
    match = re.search(r'"([^"]+)"', full_name)
    if match:
        return match.group(1).strip()
    else:
        return full_name.strip()


def main():
    setup_logging('import.log')
    logger = logging.getLogger(__name__)

    output_path_json = PROJECT_ROOT / "data" / "reference" / "companies_raw.json"
    output_path_xlsx = PROJECT_ROOT / "output" / "tables" / "companies.xlsx"

    secrets = load_secrets()

    conn = http.client.HTTPSConnection("apim.moex.com")
    payload = ''
    headers = {
        'Accept': 'application/json',
        'Authorization': r'Bearer ' + secrets['moex_alogpack']
    }
    conn.request("GET", "/iss/engines/stock/markets/shares/boards/tqbr/securities.json", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))

    df = pd.DataFrame(data["securities"]["data"], columns=data["securities"]["columns"])
    df.to_excel(output_path_xlsx, index=False)

    logger.info(f'{len(df)} компаний записано в {output_path_xlsx}')

    result = []
    for _, row in df.iterrows():
        result.append({
            row['SECID']: {
                'ticker': row['SECID'],
                'name': row['SECNAME'],
                'shortname': row['SHORTNAME'],
                'latname': row['LATNAME'],
                'isin': row['ISIN'],
                'level': row['LISTLEVEL'],
                'lotsize': int(row['LOTSIZE']),
                'minstep': int(row['MINSTEP']),
                'issuesize': int(row['ISSUESIZE']),
                'searchnames': [row['SECID'], row['ISIN'], extract_canonical_name(row['SECNAME']), row['SHORTNAME'], row['LATNAME']]
            }
        })

    with open(output_path_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f'{len(result)} компаний записано в {output_path_json}')


if __name__ == "__main__":
    main()
