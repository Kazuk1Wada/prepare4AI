#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社内スレッド投稿アプリ - 簡易版
最小限の依存関係で動作するバージョン
"""

import os
import json
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# 簡易Webフレームワーク
class SimpleApp:
    def __init__(self):
        self.routes = {}
        self.db_path = 'thread_app.db'
        self.upload_folder = 'uploads'
        os.makedirs(self.upload_folder, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ユーザーテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                dept TEXT,
                role TEXT DEFAULT 'user',
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # スレッドテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                status TEXT DEFAULT '未確認',
                like_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users (id)
            )
        ''')
        
        # コメントテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES threads (id),
                FOREIGN KEY (author_id) REFERENCES users (id)
            )
        ''')
        
        # タグテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                is_official BOOLEAN DEFAULT 0
            )
        ''')
        
        # スレッドタグテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS thread_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                FOREIGN KEY (thread_id) REFERENCES threads (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id)
            )
        ''')
        
        # いいねテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(thread_id, user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def route(self, path, methods=['GET']):
        """ルートデコレータ"""
        def decorator(func):
            self.routes[path] = {'func': func, 'methods': methods}
            return func
        return decorator
    
    def run(self, host='127.0.0.1', port=5000, debug=True):
        """アプリケーションを実行"""
        print(f"社内スレッド投稿アプリを起動中...")
        print(f"アクセス先: http://{host}:{port}")
        print(f"終了するには Ctrl+C を押してください")
        
        try:
            import http.server
            import socketserver
            from urllib.parse import urlparse, parse_qs
            
            class Handler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.handle_request()
                
                def do_POST(self):
                    self.handle_request()
                
                def handle_request(self):
                    parsed_path = urlparse(self.path)
                    path = parsed_path.path
                    
                    if path in self.app.routes:
                        route_info = self.app.routes[path]
                        if self.command in route_info['methods']:
                            try:
                                response = route_info['func'](self)
                                self.send_response(200)
                                self.send_header('Content-type', 'text/html; charset=utf-8')
                                self.end_headers()
                                self.wfile.write(response.encode('utf-8'))
                                return
                            except Exception as e:
                                print(f"エラー: {e}")
                    
                    # デフォルトのHTMLレスポンス
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = self.app.get_index_page()
                    self.wfile.write(html.encode('utf-8'))
                
                def app(self):
                    return self.server.app
            
            Handler.app = self
            
            with socketserver.TCPServer((host, port), Handler) as httpd:
                print(f"サーバーが {host}:{port} で起動しました")
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\nアプリケーションを終了します...")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
    
    def get_index_page(self):
        """メインページのHTMLを生成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # スレッド一覧を取得
        cursor.execute('''
            SELECT t.id, t.title, t.body, t.status, t.like_count, t.created_at, u.name
            FROM threads t
            JOIN users u ON t.author_id = u.id
            ORDER BY t.created_at DESC
            LIMIT 10
        ''')
        threads = cursor.fetchall()
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>社内スレッド投稿アプリ</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-comments"></i> 社内スレッド
            </a>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2>スレッド一覧</h2>
        
        <div class="row">
            <div class="col-md-8">
                {"".join([f'''
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">{thread[1]}</h5>
                        <p class="card-text">{thread[2][:200]}{"..." if len(thread[2]) > 200 else ""}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-user"></i> {thread[6]} | 
                                <i class="fas fa-clock"></i> {thread[5]} | 
                                <i class="fas fa-heart"></i> {thread[4]}
                            </small>
                            <span class="badge bg-secondary">{thread[3]}</span>
                        </div>
                    </div>
                </div>
                ''' for thread in threads])}
                
                {f'<div class="text-center py-5"><i class="fas fa-comments fa-3x text-muted mb-3"></i><h4 class="text-muted">スレッドがありません</h4><p class="text-muted">最初のスレッドを作成してみましょう！</p></div>' if not threads else ''}
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> アプリ情報</h5>
                    </div>
                    <div class="card-body">
                        <p>社内スレッド投稿アプリの簡易版です。</p>
                        <p>IT推進準備室への期待や自動化・効率化したい業務を投稿できます。</p>
                        <hr>
                        <h6>機能</h6>
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success"></i> スレッド表示</li>
                            <li><i class="fas fa-check text-success"></i> 基本UI</li>
                            <li><i class="fas fa-times text-muted"></i> ユーザー認証（開発中）</li>
                            <li><i class="fas fa-times text-muted"></i> 投稿機能（開発中）</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-light mt-5 py-4">
        <div class="container text-center">
            <p class="text-muted mb-0">&copy; 2024 社内スレッド投稿アプリ - IT推進準備室</p>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
        
        conn.close()
        return html

# アプリケーションのインスタンスを作成
app = SimpleApp()

if __name__ == '__main__':
    app.run()
