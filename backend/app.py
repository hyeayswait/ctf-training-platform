from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import db, User, Team, Challenge, Submission
from seeds import seed
import docker_runner

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ctf.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "ctf-platform-secret-key-please-change-me-32bytes-min"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    seed()


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
             team_id=team_id)
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
    return jsonify({"token": token, "username": username, "score": u.score})


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
        "static_url": c.static_url,
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

    # 已经做过的题不重复给分
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
            "rank": i,
            "username": u.username,
            "team": t.name if t else "-",
            "score": u.score,
            "solved": u.solved_count,
        })
    return jsonify(out)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
