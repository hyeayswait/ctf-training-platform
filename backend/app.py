import os
import io
import uuid
import time
from functools import wraps
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import (db, User, Team, Challenge, Submission, Hint, HintPurchase,
                Attachment, Writeup, Comment, Announcement, ContestConfig)
from seeds import seed
import docker_runner

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ctf.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "ctf-platform-secret-key-please-change-me-32bytes-min"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    seed()
    if not ContestConfig.query.first():
        db.session.add(ContestConfig(id=1, contest_name="CTF 训练赛"))
        db.session.commit()

# 提交频率限制：user_id -> [最近提交时间戳]
_submit_log = {}
SUBMIT_LIMIT = (5, 60)   # 60 秒内最多 5 次


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        u = User.query.get(int(get_jwt_identity()))
        if not u or u.role != "admin":
            return jsonify({"msg": "需要管理员权限"}), 403
        return fn(*args, **kwargs)
    return wrapper


def _contest_open():
    """比赛是否在进行中"""
    cfg = ContestConfig.query.get(1)
    now = datetime.now()
    if cfg.start_time and now < cfg.start_time:
        return False, "比赛尚未开始"
    if cfg.end_time and now > cfg.end_time:
        return False, "比赛已结束"
    return True, "ok"


def _dynamic_score(challenge):
    """根据已解人数算当前分值：线性递减，不低于 min_score"""
    solved = Submission.query.filter_by(
        challenge_id=challenge.id, is_correct=True).count()
    step = (challenge.base_score - challenge.min_score) // max(solved, 1) if solved else 0
    # 第一个人拿 base_score，之后每多一人减 step，最低 min_score
    score = max(challenge.min_score, challenge.base_score - solved * step)
    return score


# ---------- 认证 ----------
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    team_name = data.get("team", "").strip()
    if not username or not password:
        return jsonify({"msg": "用户名或密码不能为空"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "用户名已存在"}), 400
    # 防作弊：同 IP 多账号
    ip = request.remote_addr
    if User.query.filter_by(last_ip=ip).count() >= 3:
        return jsonify({"msg": "该 IP 已注册过多账号"}), 400

    team_id = None
    if team_name:
        t = Team.query.filter_by(name=team_name).first()
        if not t:
            t = Team(name=team_name); db.session.add(t); db.session.commit()
        team_id = t.id

    u = User(username=username, password_hash=generate_password_hash(password),
             team_id=team_id, role="user", last_ip=ip)
    db.session.add(u); db.session.commit()
    return jsonify({"msg": "注册成功"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"msg": "用户名或密码错误"}), 401
    u.last_ip = request.remote_addr
    db.session.commit()
    token = create_access_token(identity=str(u.id))
    return jsonify({"token": token, "username": username,
                    "score": u.score, "role": u.role})


# ---------- 比赛配置 / 公告 ----------
@app.route("/api/contest", methods=["GET"])
def get_contest():
    cfg = ContestConfig.query.get(1)
    return jsonify({
        "name": cfg.contest_name,
        "start_time": cfg.start_time.strftime("%Y-%m-%d %H:%M:%S") if cfg.start_time else None,
        "end_time": cfg.end_time.strftime("%Y-%m-%d %H:%M:%S") if cfg.end_time else None,
        "open": _contest_open()[0],
    })


@app.route("/api/admin/contest", methods=["POST"])
@admin_required
def set_contest():
    data = request.get_json() or {}
    cfg = ContestConfig.query.get(1)
    cfg.contest_name = data.get("name", cfg.contest_name)
    cfg.start_time = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S") if data.get("start_time") else None
    cfg.end_time = datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M:%S") if data.get("end_time") else None
    db.session.commit()
    return jsonify({"msg": "比赛配置已保存"})


@app.route("/api/announcements", methods=["GET"])
def list_announcements():
    items = Announcement.query.order_by(Announcement.id.desc()).all()
    return jsonify([{"id": a.id, "title": a.title, "content": a.content,
                     "created_at": a.created_at.strftime("%Y-%m-%d %H:%M")} for a in items])


@app.route("/api/admin/announcement", methods=["POST"])
@admin_required
def add_announcement():
    data = request.get_json() or {}
    db.session.add(Announcement(title=data.get("title", ""), content=data.get("content", "")))
    db.session.commit()
    return jsonify({"msg": "公告已发布"})


# ---------- 题目 ----------
@app.route("/api/challenges", methods=["GET"])
@jwt_required()
def list_challenges():
    uid = int(get_jwt_identity())
    solved_ids = {s.challenge_id for s in
                  Submission.query.filter_by(user_id=uid, is_correct=True).all()}
    q = Challenge.query

    cat = request.args.get("category", "")
    if cat:
        q = q.filter_by(category=cat)
    kw = request.args.get("q", "")
    if kw:
        q = q.filter(Challenge.title.contains(kw))
    min_score = request.args.get("min_score", type=int)
    if min_score:
        q = q.filter(Challenge.base_score >= min_score)

    out = []
    for c in q.order_by(Challenge.category, Challenge.difficulty).all():
        # Blood 标记：前 3 个解出的人
        bloods = Submission.query.filter_by(
            challenge_id=c.id, is_correct=True).order_by(Submission.submitted_at).limit(3).all()
        blood_names = []
        for b in bloods:
            bu = User.query.get(b.user_id)
            blood_names.append(bu.username if bu else "?")
        out.append({
            "id": c.id, "title": c.title, "category": c.category,
            "difficulty": c.difficulty,
            "score": _dynamic_score(c),
            "base_score": c.base_score,
            "has_docker": bool(c.docker_image),
            "has_external": bool(c.external_url),
            "solved": c.id in solved_ids,
            "bloods": blood_names,
        })
    return jsonify(out)


@app.route("/api/challenges/<int:cid>", methods=["GET"])
@jwt_required()
def challenge_detail(cid):
    c = Challenge.query.get(cid)
    if not c:
        return jsonify({"msg": "题目不存在"}), 404
    hints = Hint.query.filter_by(challenge_id=cid).all()
    uid = int(get_jwt_identity())
    bought = {h.hint_id for h in HintPurchase.query.filter_by(user_id=uid).all()}
    return jsonify({
        "id": c.id, "title": c.title, "category": c.category,
        "difficulty": c.difficulty, "description": c.description,
        "score": _dynamic_score(c),
        "external_url": c.external_url or "",
        "static_url": c.static_url or "",
        "attachments": [{"id": a.id, "filename": a.filename} for a in Attachment.query.filter_by(challenge_id=cid).all()],
        "hints": [{"id": h.id, "content": h.content if h.id in bought else "（购买后可见）",
                    "cost": h.cost, "bought": h.id in bought} for h in hints],
    })


# ---------- Flag 提交（动态分 + 频率限制） ----------
@app.route("/api/submit", methods=["POST"])
@jwt_required()
def submit():
    ok, msg = _contest_open()
    if not ok:
        return jsonify({"msg": msg}), 403

    uid = int(get_jwt_identity())
    now = time.time()
    history = [t for t in _submit_log.get(uid, []) if now - t < SUBMIT_LIMIT[1]]
    if len(history) >= SUBMIT_LIMIT[0]:
        return jsonify({"msg": "提交太频繁，请稍后再试"}), 429
    history.append(now)
    _submit_log[uid] = history

    data = request.get_json() or {}
    cid = data.get("challenge_id")
    flag_input = (data.get("flag") or "").strip()
    c = Challenge.query.get(cid)
    if not c:
        return jsonify({"msg": "题目不存在"}), 404

    already = Submission.query.filter_by(
        user_id=uid, challenge_id=cid, is_correct=True).first()
    if already:
        return jsonify({"msg": "这道题你已经拿下过了", "correct": True}), 200

    correct = (flag_input == c.flag)
    earned = _dynamic_score(c) if correct else 0
    db.session.add(Submission(user_id=uid, challenge_id=cid,
                              flag_input=flag_input, is_correct=correct,
                              earned_score=earned))
    if correct:
        u = User.query.get(uid)
        u.score += earned
        u.solved_count += 1
    db.session.commit()

    if correct:
        blood_no = Submission.query.filter_by(challenge_id=cid, is_correct=True).count()
        prefix = ""
        if blood_no == 1: prefix = "🩸 First Blood! "
        elif blood_no == 2: prefix = "🩸 Second Blood! "
        elif blood_no == 3: prefix = "🩸 Third Blood! "
        return jsonify({"correct": True, "msg": f"{prefix}回答正确 +{earned} 分",
                        "score": u.score})
    return jsonify({"correct": False, "msg": "Flag 不正确，再试试"})


# ---------- Hint ----------
@app.route("/api/hint/buy/<int:hid>", methods=["POST"])
@jwt_required()
def buy_hint(hid):
    uid = int(get_jwt_identity())
    h = Hint.query.get(hid)
    if not h:
        return jsonify({"msg": "提示不存在"}), 404
    if HintPurchase.query.filter_by(user_id=uid, hint_id=hid).first():
        return jsonify({"content": h.content, "msg": "已购买过"})
    u = User.query.get(uid)
    if u.score < h.cost:
        return jsonify({"msg": f"积分不足（需要 {h.cost} 分）"}), 400
    u.score -= h.cost
    db.session.add(HintPurchase(user_id=uid, hint_id=hid))
    db.session.commit()
    return jsonify({"content": h.content, "msg": f"已扣除 {h.cost} 分"})


# ---------- 讨论区 ----------
@app.route("/api/comment/<int:cid>", methods=["GET"])
@jwt_required()
def list_comments(cid):
    items = Comment.query.filter_by(challenge_id=cid).order_by(Comment.id).all()
    return jsonify([{
        "id": c.id, "content": c.content, "is_admin": c.is_admin,
        "username": User.query.get(c.user_id).username,
        "created_at": c.created_at.strftime("%m-%d %H:%M"),
    } for c in items])


@app.route("/api/comment/<int:cid>", methods=["POST"])
@jwt_required()
def add_comment(cid):
    uid = int(get_jwt_identity())
    u = User.query.get(uid)
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"msg": "评论不能为空"}), 400
    if "flag{" in content.lower():
        return jsonify({"msg": "禁止在讨论区发 Flag"}), 400
    db.session.add(Comment(challenge_id=cid, user_id=uid, content=content,
                            is_admin=(u.role == "admin")))
    db.session.commit()
    return jsonify({"msg": "评论已发布"})


# ---------- 排行榜 ----------
@app.route("/api/scoreboard", methods=["GET"])
def scoreboard():
    users = User.query.order_by(User.score.desc()).limit(50).all()
    out = []
    for i, u in enumerate(users, 1):
        t = Team.query.get(u.team_id) if u.team_id else None
        out.append({"rank": i, "username": u.username,
                    "team": t.name if t else "-",
                    "score": u.score, "solved": u.solved_count})
    return jsonify(out)


@app.route("/api/admin/scoreboard/export", methods=["GET"])
@admin_required
def export_scoreboard():
    import csv
    buf = io.StringIO()
    buf.write("排名,账号,战队,积分,解题数\n")
    users = User.query.order_by(User.score.desc()).all()
    for i, u in enumerate(users, 1):
        t = Team.query.get(u.team_id) if u.team_id else None
        buf.write(f"{i},{u.username},{t.name if t else '-'},{u.score},{u.solved_count}\n")
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode("utf-8-sig")),
                     mimetype="text/csv",
                     as_attachment=True, download_name="scoreboard.csv")


# ---------- 个人统计 ----------
@app.route("/api/me", methods=["GET"])
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    u = User.query.get(uid)
    solved = Submission.query.filter_by(user_id=uid, is_correct=True).all()
    cat_count = {}
    for s in solved:
        c = Challenge.query.get(s.challenge_id)
        cat_count[c.category] = cat_count.get(c.category, 0) + 1
    return jsonify({
        "username": u.username, "score": u.score,
        "solved": u.solved_count, "role": u.role,
        "by_category": cat_count,
    })


# ---------- 附件 / WriteUp / 环境 ----------
@app.route("/api/attachment/<int:fid>", methods=["GET"])
@jwt_required()
def download_attachment(fid):
    f = Attachment.query.get(fid)
    if not f: return jsonify({"msg": "附件不存在"}), 404
    return send_file(os.path.join(UPLOAD_DIR, f.stored_name),
                     as_attachment=True, download_name=f.filename)


@app.route("/api/writeup/<int:cid>", methods=["POST"])
@jwt_required()
def upload_writeup(cid):
    uid = int(get_jwt_identity())
    solved = Submission.query.filter_by(user_id=uid, challenge_id=cid, is_correct=True).first()
    if not solved:
        return jsonify({"msg": "请先解出本题再提交 WriteUp"}), 400
    note = (request.form.get("note") or "").strip()
    f = request.files.get("file")
    stored_name = filename = ""
    if f:
        ext = os.path.splitext(f.filename)[1]
        stored_name = uuid.uuid4().hex + ext
        f.save(os.path.join(UPLOAD_DIR, stored_name))
        filename = secure_filename(f.filename)
    db.session.add(Writeup(user_id=uid, challenge_id=cid,
                           filename=filename, stored_name=stored_name, content_note=note))
    db.session.commit()
    return jsonify({"msg": "WriteUp 已提交"})


@app.route("/api/writeup/<int:cid>", methods=["GET"])
@jwt_required()
def list_writeup(cid):
    ws = Writeup.query.filter_by(challenge_id=cid).order_by(Writeup.id.desc()).all()
    return jsonify([{"id": w.id, "username": User.query.get(w.user_id).username,
                     "note": w.content_note, "filename": w.filename,
                     "has_file": bool(w.stored_name),
                     "created_at": w.created_at.strftime("%Y-%m-%d %H:%M")} for w in ws])


@app.route("/api/env/start/<int:cid>", methods=["POST"])
@jwt_required()
def env_start(cid):
    uid = int(get_jwt_identity())
    c = Challenge.query.get(cid)
    if not c or not c.docker_image:
        return jsonify({"msg": "该题不需要拉起容器"}), 400
    info = docker_runner.start_env(uid, c.docker_image, c.docker_port)
    info["docker_available"] = docker_runner.docker_available()
    return jsonify(info)


@app.route("/api/env/stop/<int:cid>", methods=["POST"])
@jwt_required()
def env_stop(cid):
    docker_runner.stop_env(int(get_jwt_identity()))
    return jsonify({"msg": "环境已关闭"})


@app.route("/api/env/renew", methods=["POST"])
@jwt_required()
def env_renew():
    docker_runner.renew_env(int(get_jwt_identity()))
    return jsonify({"msg": "已续期 30 分钟"})


# ---------- 管理员：题目 CRUD ----------
@app.route("/api/admin/challenge", methods=["POST"])
@admin_required
def admin_create_challenge():
    data = request.get_json() or {}
    c = Challenge(
        title=data["title"], category=data.get("category", "web"),
        difficulty=data.get("difficulty", "easy"),
        description=data.get("description", ""), flag=data["flag"],
        base_score=int(data.get("base_score", 500)),
        min_score=int(data.get("min_score", 100)),
        score_value=int(data.get("base_score", 500)),
        docker_image=data.get("docker_image", ""),
        docker_port=int(data.get("docker_port", 0) or 0),
        external_url=data.get("external_url", ""),
        static_url=data.get("static_url", ""),
    )
    db.session.add(c); db.session.commit()
    # 可选：同时加提示
    for h in data.get("hints", []):
        db.session.add(Hint(challenge_id=c.id, content=h["content"], cost=h.get("cost", 20)))
    db.session.commit()
    return jsonify({"msg": "题目已创建", "id": c.id})


@app.route("/api/admin/challenge/<int:cid>", methods=["DELETE"])
@admin_required
def admin_delete_challenge(cid):
    c = Challenge.query.get(cid)
    if not c: return jsonify({"msg": "题目不存在"}), 404
    Hint.query.filter_by(challenge_id=cid).delete()
    Attachment.query.filter_by(challenge_id=cid).delete()
    Submission.query.filter_by(challenge_id=cid).delete()
    Writeup.query.filter_by(challenge_id=cid).delete()
    Comment.query.filter_by(challenge_id=cid).delete()
    db.session.delete(c); db.session.commit()
    return jsonify({"msg": "已删除"})


@app.route("/api/admin/challenge/<int:cid>/attachment", methods=["POST"])
@admin_required
def admin_upload_attachment(cid):
    f = request.files.get("file")
    if not f: return jsonify({"msg": "未选择文件"}), 400
    ext = os.path.splitext(f.filename)[1]
    stored = uuid.uuid4().hex + ext
    f.save(os.path.join(UPLOAD_DIR, stored))
    db.session.add(Attachment(challenge_id=cid,
                             filename=secure_filename(f.filename), stored_name=stored))
    db.session.commit()
    return jsonify({"msg": "附件已上传"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
