# 社内スレッド投稿アプリ 要求仕様書（MVP）

## 目的
社員が「IT推進準備室への期待」や「自動化・効率化したい業務」を自由に投稿できるWebアプリを構築する。  
Teamsのスレッド機能のように投稿・コメント・検索ができる仕組みをFlaskで実装する。  
将来的には生成AIによるスレッド要約や自動タグ提案を追加する。

---

## 技術構成
- 言語: Python 3.11（想定）  
- フレームワーク: Flask  
- フロント: HTML / CSS / JavaScript (Bootstrap想定)  
- DB: SQLite（初期） → PostgreSQL（本番）  
- サーバ: AWS EC2 + Nginx + Gunicorn  
- ストレージ: S3（添付ファイル格納用）

---

## ユーザー権限
| ロール | 権限 |
|--------|------|
| user | 投稿・コメント・いいね・通報 |
| moderator | タグ編集・ピン留め・ステータス変更・非公開化 |
| admin | ユーザー管理・削除・監査ログ閲覧 |

---

## 機能一覧

### 基本機能（MVP）
1. 認証（メール＋パスワード）  
2. 投稿（タイトル、本文、タグ、添付ファイル）  
3. コメント（スレッド単位）  
4. 検索（タイトル・本文・タグ）  
5. いいね（1ユーザー1回）  
6. 通報（投稿・コメント）  
7. ステータス管理（未確認／検討中／対応中／完了）  
8. タグ管理（自由タグ＋公式タグ）  
9. 通知（コメント・メンション通知）  
10. 操作ログ（AuditLog）

### 管理機能
- 投稿・コメント削除
- ユーザー権限管理
- 通報対応
- ログ確認

### 今後の拡張（AI連携）
- 投稿要約（OpenAI API）
- 自動タグ提案（Embedding）
- 類似スレッド検索（pgvector）

---

## データモデル
User(id, name, email, dept, role, password_hash)
Thread(id, title, body, author_id, status, like_count, created_at)
Comment(id, thread_id, body, author_id, created_at)
Tag(id, name)
ThreadTag(thread_id, tag_id)
Attachment(id, thread_id, file_path, mime_type)
Report(id, target_type, target_id, reason, reporter_id)
AuditLog(id, actor_id, action, target_type, target_id, created_at)


---

## API設計（例）

| メソッド | エンドポイント | 機能 |
|-----------|----------------|------|
| POST | /login | ログイン |
| GET | /threads | 投稿一覧取得 |
| POST | /threads | 投稿作成 |
| GET | /threads/{id} | 投稿詳細取得 |
| POST | /threads/{id}/comments | コメント追加 |
| POST | /threads/{id}/like | いいね登録 |
| POST | /reports | 通報送信 |
| GET | /tags | タグ一覧取得 |

---

## 画面概要

1. **ログイン画面**  
   - メール・パスワード入力  
2. **スレッド一覧画面**  
   - 検索バー、フィルタ、投稿ボタン、新着／人気切替  
3. **スレッド詳細画面**  
   - 本文・コメント一覧・いいね・タグ表示  
4. **投稿作成画面**  
   - タイトル、本文(Markdown対応)、タグ選択、添付ファイル  
5. **管理画面**  
   - 通報対応、ユーザー管理、監査ログ表示  


