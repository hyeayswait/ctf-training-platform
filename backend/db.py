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
    role = db.Column(db.String(16), default="user")   # admin / user
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
    # 方式一：平台内 Docker 拉起
    docker_image = db.Column(db.String(200), default="")
    docker_port = db.Column(db.Integer, default=0)
    # 方式二：外部靶机 URL（管理员填自己服务器地址）
    external_url = db.Column(db.String(255), default="")
    # 方式三：静态链接 / 附件
    static_url = db.Column(db.String(255), default="")
    create_time = db.Column(db.DateTime, default=datetime.now)


class Attachment(db.Model):
    """题目附件"""
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    filename = db.Column(db.String(255))        # 原始文件名
    stored_name = db.Column(db.String(255))      # 服务器上保存的随机文件名


class Submission(db.Model):
    """Flag 提交记录"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    flag_input = db.Column(db.String(255))
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.now)


class Writeup(db.Model):
    """选手 WriteUp"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    filename = db.Column(db.String(255))
    stored_name = db.Column(db.String(255))
    content_note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now)
