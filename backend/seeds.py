"""预置几道示例题目。仅在数据库为空时执行一次。"""
from db import db, Challenge, User, Team
from werkzeug.security import generate_password_hash


SAMPLE_CHALLENGES = [
    {
        "title": "Easy Web - 备份文件泄露",
        "category": "web",
        "difficulty": "easy",
        "description": "运维同学好像把源码备份忘在 Web 根目录了，访问一下看看？\n\n提示：常见备份后缀 `.bak` `.swp` `.zip`",
        "flag": "flag{b4ckup_l34k_1s_e4sy}",
        "score_value": 100,
        "docker_image": "",
        "docker_port": 0,
        "static_url": "http://127.0.0.1:8080",
    },
    {
        "title": "Misc - 伪装成图片的 ZIP",
        "category": "misc",
        "difficulty": "easy",
        "description": "下载附件，这个 JPG 好像不太对劲。\n\n提示：用 `binwalk` 或 `foremost` 分离文件尾数据。",
        "flag": "flag{jpg_zip_st3g0}",
        "score_value": 100,
        "docker_image": "",
        "docker_port": 0,
        "static_url": "",
    },
    {
        "title": "Crypto - Base64 的 N 次方",
        "category": "crypto",
        "difficulty": "medium",
        "description": "拿到一串 Base64，解出来还是 Base64，再解还是……\n\n密文：`Z3ZhZ3tDQVJUT1MtTUIzNjRfSTNfSTNfU1RBUlR9`",
        "flag": "flag{CART0-TB364_I3_I3_START}",
        "score_value": 200,
        "docker_image": "",
        "docker_port": 0,
        "static_url": "",
    },
    {
        "title": "Reverse - 一个简单的 CrackMe",
        "category": "reverse",
        "difficulty": "medium",
        "description": "下载附件，运行后输入密码就能拿到 flag。\n\n提示：用 IDA / Ghidra 看 main 函数的字符串比较。",
        "flag": "flag{r3v3rs1ng_1s_fun}",
        "score_value": 250,
        "docker_image": "",
        "docker_port": 0,
        "static_url": "",
    },
    {
        "title": "Web - 本地靶机（Docker 拉起）",
        "category": "web",
        "difficulty": "hard",
        "description": "这道题需要点击下方「启动环境」按钮，平台会为你拉起一个独立容器。\n\nFlag 在 `/flag` 文件里，请想办法读到它。",
        "flag": "flag{d0ck3r_1s0l4t3d_l4b}",
        "score_value": 400,
        "docker_image": "nginx:alpine",
        "docker_port": 80,
        "static_url": "",
    },
]


def seed():
    if Challenge.query.count() > 0:
        return
    for c in SAMPLE_CHALLENGES:
        db.session.add(Challenge(**c))
    # 建一个默认战队和管理员账号，方便演示
    t = Team(name="DemoTeam")
    db.session.add(t)
    db.session.commit()
    admin = User(username="admin",
                 password_hash=generate_password_hash("admin123"),
                 team_id=t.id)
    db.session.add(admin)
    db.session.commit()
    print(f"[seed] inserted {len(SAMPLE_CHALLENGES)} challenges, demo user admin/admin123")
