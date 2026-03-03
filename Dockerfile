# 使用官方 Python 3.11 slim 映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV PYTHONDONTWRITEBYTECODE=1

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立必要的目錄並設定權限
RUN mkdir -p data logs \
    && chmod 755 data logs

# 驗證安裝
RUN python -c "import discord; print('discord.py version:', discord.__version__)"

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import sys; import os; sys.exit(0 if os.path.exists('/app/main.py') else 1)"

# 運行應用程式
CMD ["python", "main.py"]