from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# データベース初期化
db = SQLAlchemy(app)

# ログイン管理初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'ログインが必要です。'

# アップロードフォルダ作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# データベースモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    dept = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # user, moderator, admin
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーション
    threads = db.relationship('Thread', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    reports = db.relationship('Report', backref='reporter', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='未確認')  # 未確認, 検討中, 対応中, 完了
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    comments = db.relationship('Comment', backref='thread', lazy=True, cascade='all, delete-orphan')
    attachments = db.relationship('Attachment', backref='thread', lazy=True, cascade='all, delete-orphan')
    thread_tags = db.relationship('ThreadTag', backref='thread', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='thread', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_official = db.Column(db.Boolean, default=False)  # 公式タグかどうか
    
    # リレーション
    thread_tags = db.relationship('ThreadTag', backref='tag', lazy=True)

class ThreadTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ユニーク制約
    __table_args__ = (db.UniqueConstraint('thread_id', 'user_id', name='unique_thread_user_like'),)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_type = db.Column(db.String(20), nullable=False)  # thread, comment
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='未対応')  # 未対応, 対応中, 完了
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(20))  # thread, comment, user
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ルート定義
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'new')
    
    query = Thread.query
    
    # 検索条件
    if search:
        query = query.filter(
            db.or_(
                Thread.title.contains(search),
                Thread.body.contains(search)
            )
        )
    
    # ステータスフィルタ
    if status:
        query = query.filter(Thread.status == status)
    
    # ソート
    if sort == 'popular':
        query = query.order_by(Thread.like_count.desc(), Thread.created_at.desc())
    else:  # new
        query = query.order_by(Thread.created_at.desc())
    
    threads = query.paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    return render_template('index.html', threads=threads, search=search, status=status, sort=sort)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        dept = request.form['dept']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        if password != password_confirm:
            flash('パスワードが一致しません。', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('このメールアドレスは既に登録されています。', 'error')
            return render_template('register.html')
        
        user = User(name=name, email=email, dept=dept)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('アカウントが作成されました。ログインしてください。', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/threads/<int:id>')
def thread_detail(id):
    thread = Thread.query.get_or_404(id)
    return render_template('thread_detail.html', thread=thread)

@app.route('/threads/create', methods=['GET', 'POST'])
@login_required
def create_thread():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form.getlist('tags')
        
        thread = Thread(title=title, body=body, author_id=current_user.id)
        db.session.add(thread)
        db.session.flush()  # IDを取得するため
        
        # タグの処理
        for tag_name in tags:
            if tag_name.strip():
                tag = Tag.query.filter_by(name=tag_name.strip()).first()
                if not tag:
                    tag = Tag(name=tag_name.strip())
                    db.session.add(tag)
                    db.session.flush()
                
                thread_tag = ThreadTag(thread_id=thread.id, tag_id=tag.id)
                db.session.add(thread_tag)
        
        # ファイルアップロードの処理
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + '_' + filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    attachment = Attachment(
                        thread_id=thread.id,
                        file_path=file_path,
                        original_filename=filename,
                        mime_type=file.content_type,
                        file_size=os.path.getsize(file_path)
                    )
                    db.session.add(attachment)
        
        db.session.commit()
        flash('スレッドが作成されました。', 'success')
        return redirect(url_for('thread_detail', id=thread.id))
    
    # 既存のタグを取得
    existing_tags = Tag.query.all()
    return render_template('create_thread.html', existing_tags=existing_tags)

@app.route('/threads/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_thread(id):
    thread = Thread.query.get_or_404(id)
    
    # 権限チェック
    if thread.author_id != current_user.id and current_user.role not in ['moderator', 'admin']:
        flash('このスレッドを編集する権限がありません。', 'error')
        return redirect(url_for('thread_detail', id=id))
    
    if request.method == 'POST':
        thread.title = request.form['title']
        thread.body = request.form['body']
        thread.updated_at = datetime.utcnow()
        
        # 既存のタグを削除
        ThreadTag.query.filter_by(thread_id=thread.id).delete()
        
        # 新しいタグを追加
        tags = request.form.getlist('tags')
        for tag_name in tags:
            if tag_name.strip():
                tag = Tag.query.filter_by(name=tag_name.strip()).first()
                if not tag:
                    tag = Tag(name=tag_name.strip())
                    db.session.add(tag)
                    db.session.flush()
                
                thread_tag = ThreadTag(thread_id=thread.id, tag_id=tag.id)
                db.session.add(thread_tag)
        
        db.session.commit()
        flash('スレッドが更新されました。', 'success')
        return redirect(url_for('thread_detail', id=id))
    
    existing_tags = Tag.query.all()
    current_tags = [tt.tag.name for tt in thread.thread_tags]
    return render_template('edit_thread.html', thread=thread, existing_tags=existing_tags, current_tags=current_tags)

@app.route('/threads/<int:id>/delete', methods=['POST'])
@login_required
def delete_thread(id):
    thread = Thread.query.get_or_404(id)
    
    # 権限チェック
    if thread.author_id != current_user.id and current_user.role not in ['moderator', 'admin']:
        flash('このスレッドを削除する権限がありません。', 'error')
        return redirect(url_for('thread_detail', id=id))
    
    # 添付ファイルを削除
    for attachment in thread.attachments:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
    
    db.session.delete(thread)
    db.session.commit()
    flash('スレッドが削除されました。', 'success')
    return redirect(url_for('index'))

@app.route('/threads/<int:id>/like', methods=['POST'])
@login_required
def toggle_like(id):
    thread = Thread.query.get_or_404(id)
    existing_like = Like.query.filter_by(thread_id=id, user_id=current_user.id).first()
    
    if existing_like:
        # いいねを削除
        db.session.delete(existing_like)
        thread.like_count -= 1
    else:
        # いいねを追加
        like = Like(thread_id=id, user_id=current_user.id)
        db.session.add(like)
        thread.like_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'like_count': thread.like_count,
        'liked': not existing_like
    })

@app.route('/threads/<int:thread_id>/comments', methods=['POST'])
@login_required
def add_comment(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    body = request.form['body']
    
    if not body.strip():
        flash('コメント内容を入力してください。', 'error')
        return redirect(url_for('thread_detail', id=thread_id))
    
    comment = Comment(thread_id=thread_id, body=body, author_id=current_user.id)
    db.session.add(comment)
    db.session.commit()
    
    flash('コメントが投稿されました。', 'success')
    return redirect(url_for('thread_detail', id=thread_id))

@app.route('/comments/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    
    # 権限チェック
    if comment.author_id != current_user.id and current_user.role not in ['moderator', 'admin']:
        return jsonify({'success': False, 'message': '権限がありません'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/reports', methods=['POST'])
@login_required
def create_report():
    data = request.get_json()
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    reason = data.get('reason')
    
    if not all([target_type, target_id, reason]):
        return jsonify({'success': False, 'message': '必須項目が不足しています'}), 400
    
    # 重複チェック
    existing_report = Report.query.filter_by(
        target_type=target_type,
        target_id=target_id,
        reporter_id=current_user.id
    ).first()
    
    if existing_report:
        return jsonify({'success': False, 'message': '既に通報済みです'}), 400
    
    report = Report(
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        reporter_id=current_user.id
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/download/<int:id>')
def download_file(id):
    attachment = Attachment.query.get_or_404(id)
    return send_file(attachment.file_path, as_attachment=True, download_name=attachment.original_filename)

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role not in ['moderator', 'admin']:
        flash('管理画面へのアクセス権限がありません。', 'error')
        return redirect(url_for('index'))
    
    # 統計情報
    stats = {
        'total_threads': Thread.query.count(),
        'total_comments': Comment.query.count(),
        'total_users': User.query.count(),
        'pending_reports': Report.query.filter_by(status='未対応').count()
    }
    
    # 最近の通報
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    
    return render_template('admin_panel.html', stats=stats, recent_reports=recent_reports)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
