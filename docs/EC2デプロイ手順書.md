# 社内スレッド投稿アプリ EC2デプロイ手順書

## 概要

このドキュメントでは、社内スレッド投稿アプリをAWS EC2上にデプロイする手順を説明します。

## 前提条件

- AWSアカウントを持っていること
- EC2インスタンスの基本的な操作ができること
- SSH接続の知識があること

## 1. EC2インスタンスの準備

### 1.1 インスタンスの作成

1. **AWS Management Console**にログイン
2. **EC2**サービスを選択
3. **インスタンスを起動**をクリック

### 1.2 インスタンス設定

| 項目 | 推奨設定 |
|------|----------|
| **AMI** | Amazon Linux 2023 |
| **インスタンスタイプ** | t3.micro (無料枠) または t3.small |
| **キーペア** | 新しいキーペアを作成（.pemファイルをダウンロード） |
| **セキュリティグループ** | SSH (22), HTTP (80), HTTPS (443), カスタムTCP (5000) |

### 1.3 セキュリティグループの設定

以下のポートを開放してください：

| ポート | プロトコル | ソース | 説明 |
|--------|------------|--------|------|
| 22 | SSH | 0.0.0.0/0 | SSH接続用 |
| 80 | HTTP | 0.0.0.0/0 | Webアクセス用 |
| 443 | HTTPS | 0.0.0.0/0 | HTTPS用 |
| 5000 | TCP | 0.0.0.0/0 | アプリケーション用（開発時） |

## 2. EC2インスタンスへの接続

### 2.1 SSH接続

```bash
# キーペアファイルの権限を設定
chmod 400 your-key-pair.pem

# EC2インスタンスに接続
ssh -i your-key-pair.pem ec2-user@your-ec2-public-ip
```

### 2.2 システムの更新

```bash
# システムパッケージを更新
sudo dnf update -y

# 必要なパッケージをインストール
sudo dnf install -y python3 python3-pip git
```

## 3. アプリケーションのデプロイ

### 3.1 アプリケーションディレクトリの作成

```bash
# アプリケーションディレクトリを作成
sudo mkdir -p /opt/thread-app
sudo chown ec2-user:ec2-user /opt/thread-app
cd /opt/thread-app
```

### 3.2 アプリケーションファイルのアップロード

#### 方法1: SCPを使用（推奨）

```bash
# ローカルからEC2にファイルをアップロード
scp -i your-key-pair.pem -r . ec2-user@your-ec2-public-ip:/opt/thread-app/
```

#### 方法2: Gitを使用

```bash
# Gitリポジトリからクローン（GitHub等にプッシュしている場合）
git clone https://github.com/your-username/thread-app.git .
```

### 3.3 依存関係のインストール

```bash
# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール（完全版の場合）
pip install -r requirements.txt

# または、スタンドアロン版を使用する場合は依存関係のインストールは不要
```

## 4. 本番環境用の設定

### 4.1 環境変数の設定

```bash
# 環境変数ファイルを作成
cat > .env << EOF
SECRET_KEY=your-production-secret-key-here
DATABASE_URL=sqlite:///./thread_app_prod.db
FLASK_ENV=production
EOF
```

### 4.2 アプリケーションの設定

```bash
# アプリケーションディレクトリの権限を設定
chmod 755 /opt/thread-app
chmod 644 /opt/thread-app/*.py
chmod 644 /opt/thread-app/*.json
```

## 5. プロセス管理の設定

### 5.1 systemdサービスの作成

```bash
# サービスファイルを作成
sudo tee /etc/systemd/system/thread-app.service > /dev/null << EOF
[Unit]
Description=Thread App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/thread-app
Environment=PATH=/opt/thread-app/venv/bin
ExecStart=/opt/thread-app/venv/bin/python standalone_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 サービスの有効化と開始

```bash
# systemdをリロード
sudo systemctl daemon-reload

# サービスを有効化
sudo systemctl enable thread-app

# サービスを開始
sudo systemctl start thread-app

# サービスステータスを確認
sudo systemctl status thread-app
```

## 6. Nginxの設定（リバースプロキシ）

### 6.1 Nginxのインストール

```bash
# Nginxをインストール
sudo dnf install -y nginx

# Nginxを開始
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 6.2 Nginx設定ファイルの作成

```bash
# 設定ファイルを作成
sudo tee /etc/nginx/conf.d/thread-app.conf > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;  # ドメイン名またはEC2のパブリックIP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
```

### 6.3 Nginxの再起動

```bash
# 設定をテスト
sudo nginx -t

# Nginxを再起動
sudo systemctl restart nginx
```

## 7. セキュリティの強化

### 7.1 ファイアウォールの設定

```bash
# firewalldを開始
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 必要なポートを開放
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh

# ファイアウォールを再読み込み
sudo firewall-cmd --reload
```

### 7.2 アプリケーションのポート変更

本番環境では、アプリケーションをポート80で直接提供するか、Nginxを使用することを推奨します。

## 8. ログの設定

### 8.1 ログディレクトリの作成

```bash
# ログディレクトリを作成
sudo mkdir -p /var/log/thread-app
sudo chown ec2-user:ec2-user /var/log/thread-app
```

### 8.2 ログローテーションの設定

```bash
# logrotate設定を作成
sudo tee /etc/logrotate.d/thread-app > /dev/null << EOF
/var/log/thread-app/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ec2-user ec2-user
    postrotate
        systemctl reload thread-app
    endscript
}
EOF
```

## 9. バックアップの設定

### 9.1 データベースのバックアップ

```bash
# バックアップスクリプトを作成
cat > /opt/thread-app/backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
cp /opt/thread-app/app_data.json /opt/thread-app/backups/app_data_\$DATE.json
find /opt/thread-app/backups -name "app_data_*.json" -mtime +7 -delete
EOF

# バックアップディレクトリを作成
mkdir -p /opt/thread-app/backups

# スクリプトに実行権限を付与
chmod +x /opt/thread-app/backup.sh

# 定期実行の設定（crontab）
echo "0 2 * * * /opt/thread-app/backup.sh" | crontab -
```

## 10. 監視とメンテナンス

### 10.1 ヘルスチェック

```bash
# ヘルスチェックスクリプトを作成
cat > /opt/thread-app/health_check.sh << EOF
#!/bin/bash
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    echo "OK"
else
    echo "NG"
    systemctl restart thread-app
fi
EOF

chmod +x /opt/thread-app/health_check.sh
```

### 10.2 定期メンテナンス

```bash
# システム更新の定期実行
echo "0 3 * * 0 sudo dnf update -y" | crontab -

# ログのクリーンアップ
echo "0 4 * * 0 find /var/log -name '*.log' -mtime +30 -delete" | crontab -
```

## 11. トラブルシューティング

### 11.1 よくある問題と解決方法

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| アプリケーションが起動しない | ポートが使用中 | `sudo netstat -tlnp \| grep :5000` で確認 |
| 外部からアクセスできない | セキュリティグループの設定 | EC2コンソールでセキュリティグループを確認 |
| 権限エラー | ファイルの所有者・権限 | `sudo chown -R ec2-user:ec2-user /opt/thread-app` |

### 11.2 ログの確認

```bash
# アプリケーションログの確認
sudo journalctl -u thread-app -f

# Nginxログの確認
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 12. 本番環境での注意事項

### 12.1 セキュリティ

- **SECRET_KEY**を本番用の強力なキーに変更
- 定期的なセキュリティアップデートの実施
- 不要なポートの閉鎖

### 12.2 パフォーマンス

- 必要に応じてインスタンスタイプのアップグレード
- データベースの最適化（PostgreSQLへの移行を検討）
- CDNの導入を検討

### 12.3 バックアップ

- 定期的なデータベースのバックアップ
- 設定ファイルのバックアップ
- 災害復旧計画の策定

## 13. 次のステップ

1. **ドメイン名の設定**（Route 53を使用）
2. **SSL証明書の設定**（Let's Encryptを使用）
3. **ロードバランサーの導入**（複数インスタンス運用時）
4. **監視ツールの導入**（CloudWatch等）
5. **CI/CDパイプラインの構築**

## 14. 参考リンク

- [AWS EC2公式ドキュメント](https://docs.aws.amazon.com/ec2/)
- [Nginx公式ドキュメント](https://nginx.org/en/docs/)
- [systemd公式ドキュメント](https://systemd.io/)

---

**注意**: 本手順書は基本的なデプロイ手順を説明しています。本番環境では、セキュリティ、パフォーマンス、可用性を考慮した追加の設定が必要になる場合があります。
