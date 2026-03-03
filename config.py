"""
配置文件 - 處理所有環境變數、檔案路徑和設定
"""

import os
import platform
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

# 設置日誌
logger = logging.getLogger(__name__)

# 優先從環境變數載入
ENV_FILES = [".env", ".ENV"]
for env_file in ENV_FILES:
    if Path(env_file).exists():
        load_dotenv(env_file, override=True)
        logger.debug(f"已從 {env_file} 載入環境變數")
        break

# Discord Bot 配置
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# 檔案路徑設定
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)  # 確保資料目錄存在

# 檔案路徑
REMINDERS_DATA_PATH = os.path.join(
    DATA_DIR, os.getenv("REMINDERS_DATA_FILE", "reminders.json")
)

# 檢查必要的 API 密鑰
def validate_config():
    """檢查必要的配置參數是否存在"""
    if not DISCORD_TOKEN:
        logger.warning(f"⚠️ 缺少以下環境變數: DISCORD_TOKEN")
        return False
    return True
