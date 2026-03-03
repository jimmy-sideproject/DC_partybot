# Discord PartyBot

這是一個功能精簡的 Discord 機器人，專注於提供實用的提醒與抽籤功能。

## ✨ 主要功能

- **⏰ 定時提醒 (`/remind`)**
  - 支援設定日期與時間 (YYYY-MM-DD HH:MM)
  - 支援重複模式：每天、每週、每月
  - 提醒資料持久化儲存

- **🎲 隨機抽籤 (`/draw`)**
  - 從語音頻道、文字頻道或伺服器中隨機抽取成員
  - 支援自定義抽取人數
  - 自動過濾機器人

## 🚀 快速開始

### 使用 Docker (推薦)

1. 設定環境變數：
   ```bash
   cp .env.example .env
   # 編輯 .env 填入 DISCORD_TOKEN
   ```

2. 啟動機器人：
   ```bash
   docker-compose up -d
   ```

### 本地開發

1. 安裝依賴：
   ```bash
   uv sync
   ```

2. 執行機器人：
   ```bash
   uv run python main.py
   ```

## 📝 指令列表

| 指令 | 說明 |
| --- | --- |
| `/remind` | 設定提醒 |
| `/draw` | 隨機抽取成員 |
| `/help` | 顯示幫助選單 |
