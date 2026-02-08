# Скрипт для первоначальной генерации справочника компаний из данных, получаемых по API
# После генерации файл data/reference/companies_raw.json может редактироваться вручную.
# Значение поля SecType можно найти здесь: https://www.moex.com/ru/SecuritiesListing.aspx

import pandas as pd
import logging
import http.client
import json
import re
from src.utils.config_loader import setup_logging, load_secrets, PROJECT_ROOT


def extract_name(name):
    """Извлекаем текст из двойных кавычек (если они есть)"""
    if not isinstance(name, str):
        return str(name).strip()
    match = re.search(r'"([^"]+)"', name)
    if match:
        return match.group(1).strip()
    else:
        return name.strip()

def clean_name(name):
    """Убирает ао, ап и т.д."""
    name = name.replace('-ао', '').replace(' ао', '').replace('ао', '')
    name = name.replace('-ап', '').replace(' ап', '').replace('ап', '')
    name = name.replace('"', '').replace("'", "")
    return name

def main():
    setup_logging('import.log')
    logger = logging.getLogger(__name__)

    output_path_json = PROJECT_ROOT / "data" / "raw" / "companies_raw.json"
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

    result = {}
    for _, row in df.iterrows():
        if row['SECTYPE'] == '1':
            sec_type = '_ord'
        elif row['SECTYPE'] == '2':
            sec_type = '_pref'
        else:
            sec_type = ''

        if sec_type:
            result[row['SECID']] = {
                    'name': clean_name(row['SECNAME']),
                    'ticker' + sec_type: row['SECID'],
                    'isin' + sec_type: row['ISIN'],
                    'level' + sec_type: row['LISTLEVEL'],
                    'lotsize' + sec_type: int(row['LOTSIZE']),
                    'minstep' + sec_type: int(row['MINSTEP']),
                    'issuesize' + sec_type: int(row['ISSUESIZE']),
                    'searchnames': [row['SECID'].lower(), row['ISIN'].lower(), extract_name(row['SECNAME']).lower(),
                                    row['SHORTNAME'].lower(), row['LATNAME'].lower()]
            }

    with open(output_path_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f'{len(result)} компаний записано в {output_path_json}')


if __name__ == "__main__":
    main()
