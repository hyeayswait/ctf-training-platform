from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Team(db.Model):
    """战队表"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)


class User(db.Model):
    """用户表"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    score = db.Column(db.Integer, default=0)
    solved_count = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime, default=datetime.now)


class Challenge(db.Model):
    """题目表"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(32), nullable=False)   # web / misc / crypto / reverse / pwn
    difficulty = db.Column(db.String(16), nullable=False)  # easy / medium / hard
    description = db.Column(db.Text)                       # Markdown
    flag = db.Column(db.String(128), nullable=False)
    score_value = db.Column(db.Integer, default=100)
    # 可选：需要拉起 Docker 容器的题
    docker_image = db.Column(db.String(200), default="")
    docker_port = db.Column(db.Integer, default=0)         # 容器内监听端口
    static_url = db.Column(db.String(255), default="")     # 无需容器时直接给链接


class Submission(db.Model):
    """Flag 提交记录"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    flag_input = db.Column(db.String(255))
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.now)
