#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社内スレッド投稿アプリ - スタンドアロン版
外部依存関係なしで動作するバージョン
"""

import os
import json
import http.server
import socketserver
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import threading
import time

class StandaloneApp:
    def __init__(self):
        self.port = 5000
        self.data_file = 'app_data.json'
        self.upload_folder = 'uploads'
        os.makedirs(self.upload_folder, exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """データを読み込み"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                'users': [],
                'threads': [],
                'comments': [],
                'tags': [],
                'likes': []
            }
            self.save_data()
    
    def save_data(self):
        """データを保存"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_index_page(self):
        """メインページのHTMLを生成"""
        threads_html = ""
        
        # スレッド一覧を生成（最新10件）
        recent_threads = sorted(self.data['threads'], key=lambda x: x['created_at'], reverse=True)[:10]
        
        for thread in recent_threads:
            # 作成者名を取得
            author_name = "不明"
            for user in self.data['users']:
                if user['id'] == thread['author_id']:
                    author_name = user['name']
                    break
            
            # コメント数を計算
            comment_count = sum(1 for comment in self.data['comments'] if comment['thread_id'] == thread['id'])
            
            threads_html += f'''
            <div class="card mb-3 thread-card">
                <div class="card-body">
                    <h5 class="card-title">
                        <a href="/thread/{thread['id']}" class="text-decoration-none">{thread['title']}</a>
                    </h5>
                    <p class="card-text">{thread['body'][:200]}{"..." if len(thread['body']) > 200 else ""}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-user"></i> {author_name} | 
                            <i class="fas fa-clock"></i> {thread['created_at']} | 
                            <i class="fas fa-heart"></i> {thread['like_count']} | 
                            <i class="fas fa-comments"></i> {comment_count}件
                        </small>
                        <span class="badge bg-{self.get_status_color(thread['status'])}">{thread['status']}</span>
                    </div>
                </div>
            </div>
            '''
        
        if not recent_threads:
            threads_html = '''
            <div class="text-center py-5">
                <i class="fas fa-comments fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">スレッドがありません</h4>
                <p class="text-muted">最初のスレッドを作成してみましょう！</p>
                <a href="/create" class="btn btn-primary">
                    <i class="fas fa-plus"></i> 新規投稿
                </a>
            </div>
            '''
        
        return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>社内スレッド投稿アプリ</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .thread-card {{
            transition: transform 0.2s;
        }}
        .thread-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-comments"></i> 社内スレッド
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/create">
                    <i class="fas fa-plus"></i> 新規投稿
                </a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <h2>スレッド一覧</h2>
                {threads_html}
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> アプリ情報</h5>
                    </div>
                    <div class="card-body">
                        <p>社内スレッド投稿アプリのスタンドアロン版です。</p>
                        <p>IT推進準備室への期待や自動化・効率化したい業務を投稿できます。</p>
                        <hr>
                        <div class="row text-center">
                            <div class="col-6">
                                <h4 class="text-primary">{len(self.data['threads'])}</h4>
                                <small class="text-muted">総スレッド数</small>
                            </div>
                            <div class="col-6">
                                <h4 class="text-success">{len(self.data['comments'])}</h4>
                                <small class="text-muted">総コメント数</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h5><i class="fas fa-tags"></i> 人気のタグ</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex flex-wrap gap-1">
                            <span class="badge bg-primary">IT推進</span>
                            <span class="badge bg-secondary">自動化</span>
                            <span class="badge bg-success">効率化</span>
                            <span class="badge bg-info">システム</span>
                            <span class="badge bg-warning">業務改善</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-light mt-5 py-4">
        <div class="container text-center">
            <p class="text-muted mb-0">&copy; 2025 社内スレッド投稿アプリ - IT推進準備室</p>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
    
    def get_create_page(self):
        """投稿作成ページのHTMLを生成"""
        return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新規投稿 - 社内スレッド投稿アプリ</title>
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
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="fas fa-plus"></i> 新規スレッド作成</h4>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="/create">
                            <div class="mb-3">
                                <label for="title" class="form-label">タイトル <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="title" name="title" required maxlength="200">
                                <div class="form-text">200文字以内で入力してください</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="body" class="form-label">本文 <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="body" name="body" rows="10" required placeholder="スレッドの内容を入力してください..."></textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label for="author" class="form-label">投稿者名 <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="author" name="author" required>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <a href="/" class="btn btn-secondary">
                                    <i class="fas fa-arrow-left"></i> キャンセル
                                </a>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-paper-plane"></i> 投稿
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
    
    def get_thread_detail_page(self, thread_id):
        """スレッド詳細ページのHTMLを生成"""
        thread = None
        for t in self.data['threads']:
            if t['id'] == thread_id:
                thread = t
                break
        
        if not thread:
            return '<h1>スレッドが見つかりません</h1>'
        
        # 作成者名を取得
        author_name = "不明"
        for user in self.data['users']:
            if user['id'] == thread['author_id']:
                author_name = user['name']
                break
        
        # コメント一覧を取得
        comments = [c for c in self.data['comments'] if c['thread_id'] == thread_id]
        comments_html = ""
        
        for comment in comments:
            # コメント作成者名を取得
            comment_author = "不明"
            for user in self.data['users']:
                if user['id'] == comment['author_id']:
                    comment_author = user['name']
                    break
            
            comments_html += f'''
            <div class="comment-item mb-3 pb-3 border-bottom">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-user-circle text-muted me-2"></i>
                        <div>
                            <h6 class="mb-0">{comment_author}</h6>
                            <small class="text-muted">{comment['created_at']}</small>
                        </div>
                    </div>
                </div>
                <div class="comment-content">
                    {comment['body'].replace(chr(10), '<br>')}
                </div>
            </div>
            '''
        
        if not comments:
            comments_html = '''
            <div class="text-center text-muted py-4">
                <i class="fas fa-comments fa-2x mb-2"></i>
                <p>まだコメントがありません。最初のコメントを投稿してみましょう！</p>
            </div>
            '''
        
        return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{thread['title']} - 社内スレッド投稿アプリ</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .thread-content {{
            white-space: pre-wrap;
        }}
    </style>
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
        <div class="row">
            <div class="col-md-8">
                <!-- スレッド詳細 -->
                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h2 class="mb-0">{thread['title']}</h2>
                        <span class="badge bg-{self.get_status_color(thread['status'])}">{thread['status']}</span>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-user-circle fa-2x text-muted me-2"></i>
                                <div>
                                    <h6 class="mb-0">{author_name}</h6>
                                    <small class="text-muted">投稿者</small>
                                </div>
                            </div>
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> {thread['created_at']}
                            </small>
                        </div>
                        
                        <div class="thread-content mb-3">
                            {thread['body'].replace(chr(10), '<br>')}
                        </div>
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex align-items-center">
                                <button class="btn btn-outline-danger me-2">
                                    <i class="fas fa-heart"></i> {thread['like_count']}
                                </button>
                            </div>
                            
                            <div class="text-muted">
                                <i class="fas fa-comments"></i> {len(comments)}件のコメント
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- コメント一覧 -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-comments"></i> コメント ({len(comments)}件)</h5>
                    </div>
                    <div class="card-body">
                        {comments_html}
                    </div>
                </div>
                
                <!-- コメント投稿フォーム -->
                <div class="card mt-4">
                    <div class="card-header">
                        <h5><i class="fas fa-reply"></i> コメントを投稿</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="/thread/{thread_id}/comment">
                            <div class="mb-3">
                                <label for="comment_author" class="form-label">投稿者名 <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="comment_author" name="comment_author" required>
                            </div>
                            
                            <div class="mb-3">
                                <label for="comment_body" class="form-label">コメント <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="comment_body" name="comment_body" rows="4" required placeholder="コメントを入力してください..."></textarea>
                            </div>
                            
                            <div class="d-flex justify-content-end">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-paper-plane"></i> コメント投稿
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- サイドバー -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> スレッド情報</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center mb-3">
                            <div class="col-6">
                                <h4 class="text-primary">{thread['like_count']}</h4>
                                <small class="text-muted">いいね</small>
                            </div>
                            <div class="col-6">
                                <h4 class="text-success">{len(comments)}</h4>
                                <small class="text-muted">コメント</small>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="mb-2">
                            <strong>作成者:</strong><br>
                            {author_name}
                        </div>
                        
                        <div class="mb-2">
                            <strong>作成日時:</strong><br>
                            <small class="text-muted">{thread['created_at']}</small>
                        </div>
                        
                        <div class="mb-2">
                            <strong>ステータス:</strong><br>
                            <span class="badge bg-{self.get_status_color(thread['status'])}">{thread['status']}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-light mt-5 py-4">
        <div class="container text-center">
            <p class="text-muted mb-0">&copy; 2025 社内スレッド投稿アプリ - IT推進準備室</p>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
    
    def get_status_color(self, status):
        """ステータスに応じた色を返す"""
        colors = {
            '未確認': 'secondary',
            '検討中': 'warning',
            '対応中': 'info',
            '完了': 'success'
        }
        return colors.get(status, 'secondary')
    
    def create_thread(self, title, body, author):
        """スレッドを作成"""
        thread_id = len(self.data['threads']) + 1
        
        # ユーザーIDを取得または作成
        user_id = None
        for user in self.data['users']:
            if user['name'] == author:
                user_id = user['id']
                break
        
        if not user_id:
            user_id = len(self.data['users']) + 1
            self.data['users'].append({
                'id': user_id,
                'name': author,
                'email': f"{author.lower().replace(' ', '.')}@company.com",
                'dept': '未設定',
                'role': 'user',
                'created_at': datetime.now().isoformat()
            })
        
        thread = {
            'id': thread_id,
            'title': title,
            'body': body,
            'author_id': user_id,
            'status': '未確認',
            'like_count': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.data['threads'].append(thread)
        self.save_data()
        return thread_id
    
    def create_comment(self, thread_id, body, author):
        """コメントを作成"""
        comment_id = len(self.data['comments']) + 1
        
        # ユーザーIDを取得または作成
        user_id = None
        for user in self.data['users']:
            if user['name'] == author:
                user_id = user['id']
                break
        
        if not user_id:
            user_id = len(self.data['users']) + 1
            self.data['users'].append({
                'id': user_id,
                'name': author,
                'email': f"{author.lower().replace(' ', '.')}@company.com",
                'dept': '未設定',
                'role': 'user',
                'created_at': datetime.now().isoformat()
            })
        
        comment = {
            'id': comment_id,
            'thread_id': thread_id,
            'body': body,
            'author_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        self.data['comments'].append(comment)
        self.save_data()
        return comment_id
    
    def run(self):
        """アプリケーションを実行"""
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.handle_request()
            
            def do_POST(self):
                self.handle_request()
            
            def handle_request(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                if path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = self.app.get_index_page()
                    self.wfile.write(html.encode('utf-8'))
                
                elif path == '/create':
                    if self.command == 'GET':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        html = self.app.get_create_page()
                        self.wfile.write(html.encode('utf-8'))
                    elif self.command == 'POST':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length).decode('utf-8')
                        form_data = parse_qs(post_data)
                        
                        title = form_data.get('title', [''])[0]
                        body = form_data.get('body', [''])[0]
                        author = form_data.get('author', [''])[0]
                        
                        if title and body and author:
                            thread_id = self.app.create_thread(title, body, author)
                            self.send_response(302)
                            self.send_header('Location', f'/thread/{thread_id}')
                            self.end_headers()
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'text/html; charset=utf-8')
                            self.end_headers()
                            self.wfile.write('<h1>エラー: 必須項目が入力されていません</h1>'.encode('utf-8'))
                
                elif path.startswith('/thread/') and path.count('/') == 2:
                    # スレッド詳細ページ
                    try:
                        thread_id = int(path.split('/')[2])
                        if self.command == 'GET':
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html; charset=utf-8')
                            self.end_headers()
                            html = self.app.get_thread_detail_page(thread_id)
                            self.wfile.write(html.encode('utf-8'))
                        else:
                            self.send_response(405)
                            self.send_header('Content-type', 'text/html; charset=utf-8')
                            self.end_headers()
                            self.wfile.write('<h1>405 - メソッドが許可されていません</h1>'.encode('utf-8'))
                    except ValueError:
                        self.send_response(404)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write('<h1>404 - スレッドIDが無効です</h1>'.encode('utf-8'))
                
                elif path.startswith('/thread/') and path.endswith('/comment') and path.count('/') == 3:
                    # コメント投稿
                    if self.command == 'POST':
                        try:
                            thread_id = int(path.split('/')[2])
                            content_length = int(self.headers['Content-Length'])
                            post_data = self.rfile.read(content_length).decode('utf-8')
                            form_data = parse_qs(post_data)
                            
                            comment_body = form_data.get('comment_body', [''])[0]
                            comment_author = form_data.get('comment_author', [''])[0]
                            
                            if comment_body and comment_author:
                                self.app.create_comment(thread_id, comment_body, comment_author)
                                self.send_response(302)
                                self.send_header('Location', f'/thread/{thread_id}')
                                self.end_headers()
                            else:
                                self.send_response(400)
                                self.send_header('Content-type', 'text/html; charset=utf-8')
                                self.end_headers()
                                self.wfile.write('<h1>エラー: コメント内容と投稿者名が必要です</h1>'.encode('utf-8'))
                        except ValueError:
                            self.send_response(404)
                            self.send_header('Content-type', 'text/html; charset=utf-8')
                            self.end_headers()
                            self.wfile.write('<h1>404 - スレッドIDが無効です</h1>'.encode('utf-8'))
                    else:
                        self.send_response(405)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write('<h1>405 - メソッドが許可されていません</h1>'.encode('utf-8'))
                
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write('<h1>404 - ページが見つかりません</h1>'.encode('utf-8'))
            
            def app(self):
                return self.server.app
        
        Handler.app = self
        
        try:
            with socketserver.TCPServer(("", self.port), Handler) as httpd:
                print(f"社内スレッド投稿アプリを起動中...")
                print(f"アクセス先: http://localhost:{self.port}")
                print(f"終了するには Ctrl+C を押してください")
                print("-" * 50)
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nアプリケーションを終了します...")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == '__main__':
    app = StandaloneApp()
    app.run()
