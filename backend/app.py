import os
import uuid
from functools import wraps

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import db, User, Team, Challenge, Submission, Attachment, Writeup
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
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024   # 50MB

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    seed()


# ---------- 工具 ----------
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = int(get_jwt_identity())
        u = User.query.get(uid)
        if not u or u.role != "admin":
            return jsonify({"msg": "需要管理员权限"}), 403
        return fn(*args, **kwargs)
    return wrapper


def _attachment_info(cid):
    files = Attachment.query.filter_by(challenge_id=cid).all()
    return [{"id": f.id, "filename": f.filename} for f in files]


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

    team_id = None
    if team_name:
        t = Team.query.filter_by(name=team_name).first()
        if not t:
            t = Team(name=team_name)
            db.session.add(t)
            db.session.commit()
        team_id = t.id

    u = User(username=username, password_hash=generate_password_hash(password),
             team_id=team_id, role="user")
    db.session.add(u)
    db.session.commit()
    return jsonify({"msg": "注册成功"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"msg": "用户名或密码错误"}), 401
    token = create_access_token(identity=str(u.id))
    return jsonify({"token": token, "username": username,
                    "score": u.score, "role": u.role})


# ---------- 题目 ----------
@app.route("/api/challenges", methods=["GET"])
@jwt_required()
def list_challenges():
    uid = int(get_jwt_identity())
    solved_ids = {s.challenge_id for s in
                  Submission.query.filter_by(user_id=uid, is_correct=True).all()}
    cats = Challenge.query.order_by(Challenge.category, Challenge.difficulty).all()
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "category": c.category,
        "difficulty": c.difficulty,
        "score": c.score_value,
        "has_docker": bool(c.docker_image),
        "has_external": bool(c.external_url),
        "solved": c.id in solved_ids,
    } for c in cats])


@app.route("/api/challenges/<int:cid>", methods=["GET"])
@jwt_required()
def challenge_detail(cid):
    c = Challenge.query.get(cid)
    if not c:
        return jsonify({"msg": "题目不存在"}), 404
    return jsonify({
        "id": c.id,
        "title": c.title,
        "category": c.category,
        "difficulty": c.difficulty,
        "description": c.description,
        "score": c.score_value,
        "has_docker": bool(c.docker_image),
        "external_url": c.external_url or "",
        "static_url": c.static_url or "",
        "attachments": _attachment_info(cid),
    })


# ---------- Flag 提交 ----------
@app.route("/api/submit", methods=["POST"])
@jwt_required()
def submit():
    uid = int(get_jwt_identity())
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

    ok = (flag_input == c.flag)
    db.session.add(Submission(user_id=uid, challenge_id=cid,
                              flag_input=flag_input, is_correct=ok))
    if ok:
        u = User.query.get(uid)
        u.score += c.score_value
        u.solved_count += 1
    db.session.commit()

    if ok:
        return jsonify({"correct": True, "msg": f"回答正确 +{c.score_value} 分",
                        "score": u.score})
    return jsonify({"correct": False, "msg": "Flag 不正确，再试试"})


# ---------- 排行榜 ----------
@app.route("/api/scoreboard", methods=["GET"])
def scoreboard():
    users = User.query.order_by(User.score.desc()).limit(50).all()
    out = []
    for i, u in enumerate(users, 1):
        t = Team.query.get(u.team_id) if u.team_id else None
        out.append({
            "rank": i, "username": u.username,
            "team": t.name if t else "-",
            "score": u.score, "solved": u.solved_count,
        })
    return jsonify(out)


# ---------- 附件下载 ----------
@app.route("/api/attachment/<int:fid>", methods=["GET"])
@jwt_required()
def download_attachment(fid):
    f = Attachment.query.get(fid)
    if not f:
        return jsonify({"msg": "附件不存在"}), 404
    path = os.path.join(UPLOAD_DIR, f.stored_name)
    if not os.path.exists(path):
        return jsonify({"msg": "文件丢失"}), 404
    return send_file(path, as_attachment=True, download_name=f.filename)


# ---------- WriteUp ----------
@app.route("/api/writeup/<int:cid>", methods=["POST"])
@jwt_required()
def upload_writeup(cid):
    uid = int(get_jwt_identity())
    # 必须已解出该题才能提交 WriteUp
    solved = Submission.query.filter_by(
        user_id=uid, challenge_id=cid, is_correct=True).first()
    if not solved:
        return jsonify({"msg": "请先解出本题再提交 WriteUp"}), 400

    note = (request.form.get("note") or "").strip()
    f = request.files.get("file")
    stored_name = ""
    filename = ""
    if f:
        ext = os.path.splitext(f.filename)[1]
        stored_name = uuid.uuid4().hex + ext
        f.save(os.path.join(UPLOAD_DIR, stored_name))
        filename = secure_filename(f.filename)

    w = Writeup(user_id=uid, challenge_id=cid,
                filename=filename, stored_name=stored_name,
                content_note=note)
    db.session.add(w)
    db.session.commit()
    return jsonify({"msg": "WriteUp 已提交"})


@app.route("/api/writeup/<int:cid>", methods=["GET"])
@jwt_required()
def list_writeup(cid):
    ws = Writeup.query.filter_by(challenge_id=cid).order_by(Writeup.id.desc()).all()
    return jsonify([{
        "id": w.id,
        "username": User.query.get(w.user_id).username,
        "note": w.content_note,
        "filename": w.filename,
        "has_file": bool(w.stored_name),
        "created_at": w.created_at.strftime("%Y-%m-%d %H:%M"),
    } for w in ws])


# ---------- Docker 靶机环境 ----------
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
    uid = int(get_jwt_identity())
    docker_runner.stop_env(uid)
    return jsonify({"msg": "环境已关闭"})


# ---------- 管理员：题目 CRUD ----------
@app.route("/api/admin/challenge", methods=["POST"])
@admin_required
def admin_create_challenge():
    data = request.get_json() or {}
    c = Challenge(
        title=data["title"],
        category=data.get("category", "web"),
        difficulty=data.get("difficulty", "easy"),
        description=data.get("description", ""),
        flag=data["flag"],
        score_value=int(data.get("score_value", 100)),
        docker_image=data.get("docker_image", ""),
        docker_port=int(data.get("docker_port", 0) or 0),
        external_url=data.get("external_url", ""),
        static_url=data.get("static_url", ""),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"msg": "题目已创建", "id": c.id})


@app.route("/api/admin/challenge/<int:cid>", methods=["DELETE"])
@admin_required
def admin_delete_challenge(cid):
    c = Challenge.query.get(cid)
    if not c:
        return jsonify({"msg": "题目不存在"}), 404
    Attachment.query.filter_by(challenge_id=cid).delete()
    Submission.query.filter_by(challenge_id=cid).delete()
    Writeup.query.filter_by(challenge_id=cid).delete()
    db.session.delete(c)
    db.session.commit()
    return jsonify({"msg": "已删除"})


@app.route("/api/admin/challenge/<int:cid>/attachment", methods=["POST"])
@admin_required
def admin_upload_attachment(cid):
    c = Challenge.query.get(cid)
    if not c:
        return jsonify({"msg": "题目不存在"}), 404
    f = request.files.get("file")
    if not f:
        return jsonify({"msg": "未选择文件"}), 400
    ext = os.path.splitext(f.filename)[1]
    stored_name = uuid.uuid4().hex + ext
    f.save(os.path.join(UPLOAD_DIR, stored_name))
    a = Attachment(challenge_id=cid,
                   filename=secure_filename(f.filename),
                   stored_name=stored_name)
    db.session.add(a)
    db.session.commit()
    return jsonify({"msg": "附件已上传", "filename": a.filename})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
