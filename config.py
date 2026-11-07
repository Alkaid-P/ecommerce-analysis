# config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "system.db"

# === 新增日志目录配置 ===
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "system.log"
# ========================

RAW_DATA_FILE = RAW_DATA_DIR / "online_retail.csv"
CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "cleaned_data.csv"
USER_FEATURE_FILE = PROCESSED_DATA_DIR / "user_features.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2
DEFAULT_CLUSTER_K = 4
RFM_BINS = 5


def ensure_dirs() -> None:
    """创建项目运行所需目录。"""
    # 添加了 LOG_DIR
    for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODEL_DIR, DATABASE_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)