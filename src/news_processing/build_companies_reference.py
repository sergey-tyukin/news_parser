# Скрипт для первоначальной генерации справочника компаний из Listing.xlsx.
# После генерации файл data/reference/companies.json может редактироваться вручную.

import re
import json
from pathlib import Path
import pandas as pd

from src.utils.config_loader import PROJECT_ROOT


def extract_canonical_name(full_name: str) -> str:
    """Извлекает текст из двойных кавычек, если есть; иначе возвращает строку как есть."""
    if not isinstance(full_name, str):
        return str(full_name).strip()
    match = re.search(r'"([^"]+)"', full_name)
    if match:
        return match.group(1).strip()
    else:
        return full_name.strip()


def build_companies_reference(
        input_path: Path,
        output_path: Path,
        filter_by_supertype: bool = True,
        supertype_value: str = "Акции"
):
    """
    Генерирует справочник компаний из Excel-файла.

    Args:
        input_path: путь к Listing.xlsx
        output_path: путь для сохранения companies.json
        filter_by_supertype: если True — обрабатывать только строки с SUPERTYPE == supertype_value
        supertype_value: значение SUPERTYPE для фильтрации (по умолчанию "Акции")
    """
    df = pd.read_excel(input_path, dtype=str)

    # Удаляем строки, где TRADE_CODE или EMITENT_FULL_NAME отсутствуют
    df = df.dropna(subset=["TRADE_CODE", "EMITENT_FULL_NAME"])

    if filter_by_supertype:
        if "SUPERTYPE" not in df.columns:
            raise ValueError("Колонка 'SUPERTYPE' отсутствует в файле, но включена фильтрация.")
        initial_count = len(df)
        df = df[df["SUPERTYPE"] == supertype_value]
        filtered_count = len(df)
        print(f"Фильтрация по SUPERTYPE='{supertype_value}': {initial_count} → {filtered_count} строк")

    companies_dict = {}

    for _, row in df.iterrows():
        ticker = str(row["TRADE_CODE"]).strip()
        full_name = row["EMITENT_FULL_NAME"]

        canonical = extract_canonical_name(full_name)

        if not canonical:
            continue

        aliases = [ticker, canonical]

        if canonical in companies_dict:
            # Объединяем алиасы без дублей
            companies_dict[canonical] = list(set(companies_dict[canonical] + aliases))
        else:
            companies_dict[canonical] = aliases

    # Сохранение
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(companies_dict, f, ensure_ascii=False, indent=2)

    print(f"Справочник сохранён: {output_path}")
    print(f"Обработано компаний: {len(companies_dict)}")


def main():
    input_path = PROJECT_ROOT / "data" / "raw" / "Listing.xlsx"
    output_path = PROJECT_ROOT / "data" / "reference" / "companies.json"

    # Основной вызов — только акции
    build_companies_reference(
        input_path=input_path,
        output_path=output_path,
        filter_by_supertype=True,  # ← можно поставить False, чтобы отключить фильтр
        supertype_value="Акции"
    )


if __name__ == "__main__":
    main()