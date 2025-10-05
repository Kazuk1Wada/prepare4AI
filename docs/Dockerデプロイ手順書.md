# 社内スレッド投稿アプリ Dockerデプロイ手順書

## 概要

このドキュメントでは、Dockerを使用して社内スレッド投稿アプリをEC2上にデプロイする手順を説明します。Dockerを使用することで、環境の一貫性を保ち、デプロイを簡単にできます。

## 前提条件

- AWSアカウントを持っていること
- Dockerの基本的な知識があること
- EC2インスタンスの基本的な操作ができること

## 1. Dockerfileの作成

### 1.1 スタンドアロン版用Dockerfile

```dockerfile
# Dockerfile
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

# アプリケーションを実行
CMD ["python", "standalone_app.py"]
```

### 1.2 完全版用Dockerfile

```dockerfile
# Dockerfile.full
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY app.py .
COPY config.py .
COPY templates/ ./templates/
COPY static/ ./static/

# アプリケーションディレクトリを作成
RUN mkdir -p uploads instance

# ポート5000を公開
EXPOSE 5000

# アプリケーションを実行
CMD ["python", "app.py"]
```

## 2. Docker Composeファイルの作成

### 2.1 docker-compose.yml

```yaml
version: '3.8'

services:
  thread-app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-production-secret-key
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - thread-app
    restart: unless-stopped
```

### 2.2 nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream thread_app {
        server thread-app:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://thread_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 3. EC2インスタンスの準備

### 3.1 インスタンスの作成

1. **AWS Management Console**にログイン
2. **EC2**サービスを選択
3. **インスタンスを起動**をクリック

### 3.2 インスタンス設定

| 項目 | 推奨設定 |
|------|----------|
| **AMI** | Amazon Linux 2023 |
| **インスタンスタイプ** | t3.micro (無料枠) または t3.small |
| **キーペア** | 新しいキーペアを作成 |
| **セキュリティグループ** | SSH (22), HTTP (80), HTTPS (443) |

### 3.3 セキュリティグループの設定

| ポート | プロトコル | ソース | 説明 |
|--------|------------|--------|------|
| 22 | SSH | 0.0.0.0/0 | SSH接続用 |
| 80 | HTTP | 0.0.0.0/0 | Webアクセス用 |
| 443 | HTTPS | 0.0.0.0/0 | HTTPS用 |

## 4. EC2インスタンスへの接続とセットアップ

### 4.1 SSH接続

```bash
# キーペアファイルの権限を設定
chmod 400 your-key-pair.pem

# EC2インスタンスに接続
ssh -i your-key-pair.pem ec2-user@your-ec2-public-ip
```

### 4.2 Dockerのインストール

```bash
# システムパッケージを更新
sudo dnf update -y

# Dockerをインストール
sudo dnf install -y docker

# Dockerサービスを開始
sudo systemctl start docker
sudo systemctl enable docker

# ec2-userをdockerグループに追加
sudo usermod -a -G docker ec2-user

# ログアウトして再ログイン（グループ変更を反映）
exit
```

### 4.3 Docker Composeのインストール

```bash
# Docker Composeをインストール
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 実行権限を付与
sudo chmod +x /usr/local/bin/docker-compose

# シンボリックリンクを作成
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

## 5. アプリケーションのデプロイ

### 5.1 アプリケーションディレクトリの作成

```bash
# アプリケーションディレクトリを作成
mkdir -p /home/ec2-user/thread-app
cd /home/ec2-user/thread-app
```

### 5.2 アプリケーションファイルのアップロード

#### 方法1: SCPを使用

```bash
# ローカルからEC2にファイルをアップロード
scp -i your-key-pair.pem -r . ec2-user@your-ec2-public-ip:/home/ec2-user/thread-app/
```

#### 方法2: Gitを使用

```bash
# Gitリポジトリからクローン
git clone https://github.com/your-username/thread-app.git .
```

### 5.3 データディレクトリの作成

```bash
# データディレクトリを作成
mkdir -p data uploads ssl

# 初期データファイルを作成
cat > data/app_data.json << EOF
{
  "users": [],
  "threads": [],
  "comments": [],
  "tags": [],
  "likes": []
}
EOF
```

## 6. アプリケーションの起動

### 6.1 Dockerイメージのビルド

```bash
# スタンドアロン版の場合
docker build -t thread-app .

# 完全版の場合
docker build -f Dockerfile.full -t thread-app .
```

### 6.2 Docker Composeで起動

```bash
# アプリケーションを起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

### 6.3 動作確認

```bash
# アプリケーションのステータスを確認
docker-compose ps

# ヘルスチェック
curl http://localhost:5000
```

## 7. 本番環境用の設定

### 7.1 環境変数の設定

```bash
# .envファイルを作成
cat > .env << EOF
SECRET_KEY=your-production-secret-key-here
FLASK_ENV=production
DATABASE_URL=sqlite:///./data/thread_app_prod.db
EOF
```

### 7.2 SSL証明書の設定（Let's Encrypt）

```bash
# Certbotをインストール
sudo dnf install -y certbot

# SSL証明書を取得
sudo certbot certonly --standalone -d your-domain.com

# 証明書をコピー
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
```

### 7.3 HTTPS対応のNginx設定

```bash
# HTTPS対応のnginx.confを作成
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream thread_app {
        server thread-app:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://\$server_name\$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        location / {
            proxy_pass http://thread_app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
```

## 8. バックアップとメンテナンス

### 8.1 バックアップスクリプトの作成

```bash
# バックアップスクリプトを作成
cat > backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ec2-user/backups"
mkdir -p \$BACKUP_DIR

# データベースのバックアップ
cp data/app_data.json \$BACKUP_DIR/app_data_\$DATE.json

# 古いバックアップを削除（7日以上前）
find \$BACKUP_DIR -name "app_data_*.json" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x backup.sh
```

### 8.2 定期バックアップの設定

```bash
# crontabにバックアップタスクを追加
echo "0 2 * * * /home/ec2-user/thread-app/backup.sh" | crontab -
```

### 8.3 ログローテーションの設定

```bash
# Docker Composeでログローテーションを設定
cat > docker-compose.override.yml << EOF
version: '3.8'

services:
  thread-app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

## 9. 監視とヘルスチェック

### 9.1 ヘルスチェックスクリプト

```bash
# ヘルスチェックスクリプトを作成
cat > health_check.sh << EOF
#!/bin/bash
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    echo "OK"
else
    echo "NG - Restarting application"
    docker-compose restart thread-app
fi
EOF

chmod +x health_check.sh

# 定期ヘルスチェックの設定
echo "*/5 * * * * /home/ec2-user/thread-app/health_check.sh" | crontab -
```

### 9.2 ログ監視

```bash
# ログ監視スクリプト
cat > log_monitor.sh << EOF
#!/bin/bash
# エラーログを監視
docker-compose logs --tail=100 thread-app | grep -i error | tail -10
EOF

chmod +x log_monitor.sh
```

## 10. 更新とデプロイ

### 10.1 アプリケーションの更新

```bash
# 新しいバージョンをデプロイ
git pull origin main

# イメージを再ビルド
docker-compose build

# アプリケーションを再起動
docker-compose up -d
```

### 10.2 ゼロダウンタイムデプロイ

```bash
# ブルーグリーンデプロイ用のスクリプト
cat > deploy.sh << EOF
#!/bin/bash
# 新しいイメージをビルド
docker-compose build

# 新しいコンテナを起動
docker-compose up -d --scale thread-app=2

# 古いコンテナを停止
docker-compose up -d --scale thread-app=1

echo "Deployment completed"
EOF

chmod +x deploy.sh
```

## 11. トラブルシューティング

### 11.1 よくある問題と解決方法

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| コンテナが起動しない | ポートの競合 | `docker-compose down` で停止後、再起動 |
| データが保存されない | ボリュームマウントの問題 | `docker-compose logs` でログを確認 |
| 外部からアクセスできない | セキュリティグループの設定 | EC2コンソールでポート80を開放 |

### 11.2 ログの確認

```bash
# アプリケーションログの確認
docker-compose logs -f thread-app

# Nginxログの確認
docker-compose logs -f nginx

# システムログの確認
sudo journalctl -f
```

## 12. セキュリティの強化

### 12.1 ファイアウォールの設定

```bash
# firewalldを設定
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 必要なポートのみ開放
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 12.2 定期的なセキュリティアップデート

```bash
# セキュリティアップデートの自動実行
echo "0 3 * * 0 sudo dnf update -y && docker-compose restart" | crontab -
```

## 13. パフォーマンスの最適化

### 13.1 リソース制限の設定

```yaml
# docker-compose.ymlに追加
services:
  thread-app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### 13.2 キャッシュの設定

```bash
# Redisを追加（オプション）
cat >> docker-compose.yml << EOF

  redis:
    image: redis:alpine
    restart: unless-stopped
EOF
```

## 14. 参考リンク

- [Docker公式ドキュメント](https://docs.docker.com/)
- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [Nginx公式ドキュメント](https://nginx.org/en/docs/)

---

**注意**: 本手順書は基本的なDockerデプロイ手順を説明しています。本番環境では、セキュリティ、パフォーマンス、可用性を考慮した追加の設定が必要になる場合があります。
