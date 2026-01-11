import yaml
from pathlib import Path
from logging.config import dictConfig

PROJECT_ROOT = Path(__file__).parent.parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
SECRETS_PATH = CONFIG_DIR / "secrets.yaml"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


def load_yaml(path: Path):
    """Вспомогательная функция для безопасной загрузки YAML."""
    if not path.exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {path}")
    with Path.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config():
    """Загружает основной конфиг (без секретов)."""
    return load_yaml(CONFIG_PATH)


def load_secrets():
    """Загружает секреты. Вызывает исключение, если файл отсутствует."""
    return load_yaml(SECRETS_PATH)


def setup_logging(log_file):
    config = load_config()
    log_path = (PROJECT_ROOT / "logs" / log_file).resolve()
    config["logging"]["handlers"]["file"]["filename"] = str(log_path)
    dictConfig(config["logging"])
