import json

from src.utils.config_loader import PROJECT_ROOT


def print_news():
    input_file = PROJECT_ROOT / "data" / "processed" / "news_sentiment.json"
    output_file = PROJECT_ROOT / "data" / "processed" / "clean_news.json"

    with open(input_file, 'r', encoding='utf-8') as f:
        news = json.load(f)

    filtered_news = [
        item for item in news
        if item.get("mentioned_companies")
           and item.get("sentiment_label") in ("positive", "negative")
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_news, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print_news()
