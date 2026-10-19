from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    score = db.Column(db.Integer, default=0)
    solved_count = db.Column(db.Integer, default=0)
    role = db.Column(db.String(16), default="user")
    last_ip = db.Column(db.String(64), default="")
    create_time = db.Column(db.DateTime, default=datetime.now)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    difficulty = db.Column(db.String(16), nullable=False)
    description = db.Column(db.Text)
    flag = db.Column(db.String(128), nullable=False)
    score_value = db.Column(db.Integer, default=100)        # 兼容旧字段
    base_score = db.Column(db.Integer, default=500)          # 动态分：起始分
    min_score = db.Column(db.Integer, default=100)           # 动态分：最低分
    docker_image = db.Column(db.String(200), default="")
    docker_port = db.Column(db.Integer, default=0)
    external_url = db.Column(db.String(255), default="")
    static_url = db.Column(db.String(255), default="")
    create_time = db.Column(db.DateTime, default=datetime.now)


class Hint(db.Model):
    """题目提示：花分购买"""
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    content = db.Column(db.Text)
    cost = db.Column(db.Integer, default=20)   # 买这条提示扣多少分


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    filename = db.Column(db.String(255))
    stored_name = db.Column(db.String(255))


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    flag_input = db.Column(db.String(255))
    is_correct = db.Column(db.Boolean, default=False)
    earned_score = db.Column(db.Integer, default=0)   # 动态分：本次实际得分
    submitted_at = db.Column(db.DateTime, default=datetime.now)


class HintPurchase(db.Model):
    """用户买过哪些提示"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hint_id = db.Column(db.Integer, db.ForeignKey('hint.id'), nullable=False)
    bought_at = db.Column(db.DateTime, default=datetime.now)


class Writeup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    filename = db.Column(db.String(255))
    stored_name = db.Column(db.String(255))
    content_note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now)


class Comment(db.Model):
    """题目讨论区"""
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Announcement(db.Model):
    """公告"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class ContestConfig(db.Model):
    """比赛配置（单行表）"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    contest_name = db.Column(db.String(200), default="CTF 训练赛")
