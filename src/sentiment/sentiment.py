import json
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

from src.utils.config_loader import setup_logging, PROJECT_ROOT


def get_sentiment():
    input_file = PROJECT_ROOT / "data" / "raw" / "news.json"
    output_file = PROJECT_ROOT / "data" / "processed" / "news_sentiment.json"

    setup_logging("sentiment.log")
    logger = logging.getLogger(__name__)

    model_name = PROJECT_ROOT / "src" / "sentiment" / ".rubert-tiny2-russian-financial-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    classifier = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        device=-1  # явно указываем, что считаем на CPU
    )

    with open(input_file, "r", encoding="utf-8") as f:
        news_list = json.load(f)

    results = []
    for item in news_list:
        text = item["text"]

        try:
            result = classifier(text)[0]
            sentiment = {
                "channel": item["channel"],
                "message_id": item["message_id"],
                "text": text,
                "date": item["date"],
                "link": item["link"],
                "sentiment_label": result["label"],
                "sentiment_score": round(result["score"], 4)
            }
            results.append(sentiment)
        except Exception as e:
            logger.error(f"Ошибка при обработке новости {item['message_id']}: {e}")
            continue

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"Анализ завершён. Результаты сохранены в {output_file}")


if __name__ == '__main__':
    get_sentiment()
