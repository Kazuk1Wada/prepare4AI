# 社内スレッド投稿アプリ - スタンドアロン版用Dockerfile
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションファイルをコピー
COPY standalone_app.py .
COPY app_data.json* ./

# アプリケーションディレクトリを作成
RUN mkdir -p uploads

# ポート5000を公開
EXPOSE 5000

# ヘルスチェックを追加
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000 || exit 1

# アプリケーションを実行
CMD ["python", "standalone_app.py"]
