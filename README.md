# DC PartyBot 🎉

這是一個專為社群互動設計的 Discord 機器人，提供實用的定時提醒與隨機抽籤功能。採用 Python 編寫，支援 Docker 快速部署。

## ✨ 主要功能

### ⏰ 智能提醒系統
- **設定提醒**：支援指定日期與時間發送提醒訊息。
- **循環模式**：可設定「每天」、「每週」或「每月」重複提醒。
- **持久化儲存**：提醒事項會儲存在本地檔案中，重啟機器人也不會遺失。
- **管理功能**：使用者可以隨時查看或刪除自己設定的提醒。

### 🎲 隨機抽籤工具
- **多種來源**：
  - 🔊 **目前語音頻道**：從你所在的語音頻道中抽取。
  - 📝 **目前文字頻道**：從目前頻道的成員中抽取。
  - 🏰 **整個伺服器**：從伺服器所有成員中抽取。
- **智慧過濾**：自動排除機器人帳號，確保只抽出真實用戶。
- **自訂人數**：一次可抽取多名幸運兒。

## 🛠️ 安裝與設置

您可以選擇使用 Docker（推薦）或直接在本地運行 Python 環境。

### 前置作業

1. 取得 Discord Bot Token：
   - 前往 [Discord Developer Portal](https://discord.com/developers/applications)。
   - 建立新的 Application 並新增 Bot。
   - 複製 Token。
2. 開啟 **Message Content Intent**：
   - 在 Bot 設定頁面中，將 `MESSAGE CONTENT INTENT` 選項開啟。
   - 將機器人邀請至您的伺服器。

### 方法一：使用 Docker (推薦) 🐳

最簡單的部署方式，不需要安裝 Python 環境。

1. **複製專案**
   ```bash
   git clone <你的 repo url>
   cd DC_meetbot
   ```

2. **設定環境變數**
   建立 `.env` 檔案（可參考 `.env.example`）：
   ```bash
   # Linux/Mac
   cp .env.example .env
   # Windows
   copy .env.example .env
   ```
   編輯 `.env` 檔案，填入您的 Token：
   ```env
   DISCORD_TOKEN=你的_DISCORD_BOT_TOKEN
   COMMAND_PREFIX=!
   ```

3. **啟動服務**
   ```bash
   docker-compose up -d
   ```

### 方法二：本地開發 (Python) 🐍

適合開發者或想要直接運行的使用者。

1. **安裝依賴**
   本專案使用 `uv` 進行套件管理，但也支援傳統 pip。

   **使用 uv (推薦):**
   ```bash
   uv sync
   ```

   **使用 pip:**
   ```bash
   pip install -r requirements.txt
   # 如果沒有 requirements.txt，可依據 pyproject.toml 安裝:
   pip install discord.py python-dotenv certifi
   ```

2. **設定環境變數**
   同上，建立 `.env` 檔案並填入 `DISCORD_TOKEN`。

3. **執行機器人**
   ```bash
   # 使用 uv
   uv run python main.py

   # 使用 python
   python main.py
   ```

## 📝 指令列表

本機器人使用 Discord 斜線指令 (Slash Commands)。

| 指令 | 參數 | 說明 |
| :--- | :--- | :--- |
| `/remind` | `time_str`: 時間 (MM-DD HH:MM)<br>`message`: 提醒內容<br>`repeat_mode`: 重複模式 | 設定一個新的提醒 |
| `/list_reminders` | 無 | 列出您設定的所有提醒 |
| `/delete_reminder` | `index`: 提醒編號 | 刪除指定的提醒（編號請參照 list 指令） |
| `/draw` | `count`: 人數<br>`source`: 來源 (語音/文字/伺服器) | 隨機抽取成員 |

> **注意**：時間格式支援 `YYYY-MM-DD HH:MM` 或 `MM-DD HH:MM`（自動帶入今年）。

## 📂 專案結構

```
.
├── config.py           # 配置管理
├── docker-compose.yml  # Docker 部署設定
├── Dockerfile          # Docker 建置檔
├── main.py             # 程式進入點
├── pyproject.toml      # 專案依賴與設定
├── README.md           # 說明文件
├── utils_cog.py        # 主要功能模組 (提醒、抽籤)
├── data/               # 資料儲存目錄
│   └── reminders.json  # 提醒事項資料庫
└── logs/               # 運行日誌
```

## 🤝 貢獻代碼

歡迎提交 Pull Request 或 Issue 來改進功能！

1. Fork 本專案
2. 建立新分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT License。
