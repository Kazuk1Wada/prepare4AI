# 社内スレッド投稿アプリ

社員が「IT推進準備室への期待」や「自動化・効率化したい業務」を自由に投稿できるWebアプリケーションです。

## 機能

### 基本機能（MVP）
- ユーザー認証（メール＋パスワード）
- スレッド投稿（タイトル、本文、タグ、添付ファイル）
- コメント機能
- 検索・フィルタ機能
- いいね機能
- 通報機能
- ステータス管理（未確認／検討中／対応中／完了）
- タグ管理（自由タグ＋公式タグ）
- 管理画面

### 技術構成
- **言語**: Python 3.11
- **フレームワーク**: Flask
- **フロントエンド**: HTML / CSS / JavaScript (Bootstrap 5)
- **データベース**: SQLite（開発） → PostgreSQL（本番）
- **認証**: Flask-Login
- **ファイルアップロード**: Werkzeug

## セットアップ

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境設定
`env_example.txt`を参考に`.env`ファイルを作成し、必要な設定を行ってください。

### 3. データベースの初期化
```bash
python app.py
```

初回実行時にデータベースが自動作成されます。

### 4. アプリケーションの起動
```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセスしてください。

## 使用方法

### ユーザー登録
1. トップページの「新規登録」をクリック
2. 必要事項を入力してアカウントを作成
3. ログインしてスレッドを投稿

### スレッド投稿
1. ログイン後、「新規投稿」をクリック
2. タイトル、本文、タグを入力
3. 必要に応じてファイルを添付
4. 「投稿」ボタンで公開

### 管理機能
- 管理者権限でログイン後、「管理画面」から各種管理機能にアクセス可能
- 通報対応、ユーザー管理、統計確認などが可能

## ディレクトリ構造

```
prepare4AI/
├── app.py                 # メインアプリケーション
├── config.py             # 設定ファイル
├── requirements.txt      # 依存関係
├── templates/            # HTMLテンプレート
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── thread_detail.html
│   ├── create_thread.html
│   ├── edit_thread.html
│   └── admin_panel.html
├── static/               # 静的ファイル
├── uploads/              # アップロードファイル
└── docs/                 # ドキュメント
    └── 要求仕様書_MVP.md
```

## デプロイ手順

### EC2へのデプロイ

詳細なデプロイ手順は以下のドキュメントを参照してください：

- **[EC2デプロイ手順書](docs/EC2デプロイ手順書.md)**: 従来の方法でのEC2デプロイ
- **[Dockerデプロイ手順書](docs/Dockerデプロイ手順書.md)**: Dockerを使用した簡単なデプロイ

### クイックスタート（Docker）

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd thread-app

# 2. データディレクトリを作成
mkdir -p data uploads ssl

# 3. Docker Composeで起動
docker-compose up -d

# 4. ブラウザでアクセス
# http://localhost:5000
```

## 今後の拡張予定

- 生成AIによるスレッド要約機能
- 自動タグ提案機能
- 類似スレッド検索機能
- メール通知機能
- リアルタイム通知機能

## アプリケーションの種類

このプロジェクトには2つのバージョンが含まれています：

### 1. 完全版（app.py）
- **特徴**: Flaskベースの本格的なWebアプリケーション
- **依存関係**: 外部ライブラリが必要（Flask、SQLAlchemy等）
- **データベース**: SQLite（リレーショナルデータベース）
- **機能**: 要求仕様書の全機能を実装
- **用途**: 本格的な運用・開発

### 2. スタンドアロン版（standalone_app.py）
- **特徴**: 外部依存関係なしで動作する簡易版
- **依存関係**: Python標準ライブラリのみ
- **データベース**: JSONファイル
- **機能**: 基本的なスレッド表示・投稿機能
- **用途**: 学習・理解・プロトタイプ

### 使い分け

| 状況 | 推奨バージョン | 理由 |
|------|----------------|------|
| 学習・理解したい | standalone_app.py | 依存関係なし、シンプル |
| 環境に問題がある | standalone_app.py | 確実に動作する |
| 本格的な開発 | app.py | 全機能、拡張性 |
| プロダクション運用 | app.py | セキュリティ、性能 |

### 起動方法

#### スタンドアロン版（推奨：環境問題がある場合）

**初回起動**
```bash
python standalone_app.py
```

**再起動手順**
```powershell
# 1. 現在のプロセスを確認
netstat -ano | findstr :5000

# 2. 実行中のプロセスを停止（PIDは上記コマンドで確認した番号）
taskkill /PID [プロセスID] /F

# 3. アプリケーションを再起動
python standalone_app.py
```

**バックグラウンド実行**
```powershell
# 新しいPowerShellウィンドウで起動
Start-Process python -ArgumentList "standalone_app.py"

# または、現在のウィンドウでバックグラウンド実行
Start-Job -ScriptBlock { python standalone_app.py }
```

**アクセス方法**
- ブラウザで `http://localhost:5000` にアクセス
- アプリケーションが正常に起動すると、スレッド一覧が表示されます

**トラブルシューティング**

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| ポートが使用中エラー | 既にアプリが起動中 | `netstat -ano \| findstr :5000` でプロセスを確認し、`taskkill /PID [PID] /F` で停止 |
| アクセスできない | アプリが起動していない | `python standalone_app.py` で起動を確認 |
| データが保存されない | 権限問題 | アプリケーションディレクトリの書き込み権限を確認 |

#### 完全版（依存関係が解決できている場合）
```bash
pip install -r requirements.txt
python app.py
```

## ライセンス

このプロジェクトは社内利用を目的としています。