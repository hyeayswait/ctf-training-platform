# 🚩 CTF Training Platform

[![Vue3](https://img.shields.io/badge/frontend-Vue%203-42b883)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/backend-Flask-000000)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/deploy-Docker%20Compose-2496ed)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A full-featured, self-hosted CTF training & competition platform for classes, clubs and skill contests.
Comes with **100 built-in challenges**, **dynamic scoring**, **Docker ephemeral labs**, hints, scoreboard, write-up uploads and more.

> 🎓 For educational use only. Run it on your own servers / in your own lab.

---

## ✨ Features

### Core
- 🔐 User register / login (JWT, hashed passwords, team support)
- 📚 **100 built-in challenges** across Web / Misc / Crypto / Reverse
- 🚩 Flag submission with auto-judging, anti-duplicate scoring
- 🏆 Live scoreboard (top 50), CSV export
- 🎨 Dark hacker theme with Element Plus

### Competition Logic
- 📈 **Dynamic scoring** — first blood scores more, score drops as more people solve
- 🩸 **First / Second / Third Blood** badges with celebration messages
- 💡 **Hint system** — spend points to buy hints
- ⏳ **Contest countdown** — configurable start / end time window
- 📢 Announcement banner
- 🛡 Anti-cheat — same-IP registration limit, submit rate limiting

### Target / Lab
- 🐳 **One-click ephemeral Docker environments** per user, auto-cleanup after 30 min, one-click renew
- 🌐 **External target URL** — point to your own server's challenge without bundling a Docker image
- 📎 Challenge attachments (upload / download)

### Collaboration
- 💬 Per-challenge discussion board (auto-blocks flag leaks)
- 📝 Write-up upload after solving
- 📊 Personal solve radar chart (category distribution)

### Admin
- 🛠 Web admin panel — create / delete challenges, upload attachments
- ⏱ Contest time window configuration
- 📢 Publish announcements
- 🎯 Configure dynamic score (base / min), difficulty, hints

---

## 🚀 Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py                       # http://127.0.0.1:5000

# Frontend
cd frontend
npm install
npm run dev                         # http://127.0.0.1:5173

# Or Docker Compose
docker compose up -d --build
# frontend http://127.0.0.1:8080
```

Demo account: **admin / admin123** (role = admin)

## 🏗 Tech Stack

| Layer | Tech |
| --- | --- |
| Frontend | Vue 3 + Vite + Element Plus + ECharts + Axios |
| Backend | Flask + Flask-JWT-Extended + SQLAlchemy |
| Database | SQLite |
| Labs | docker SDK (ephemeral containers) |
| Export | CSV scoreboard |

## 📂 Structure

```
ctf-platform/
├── backend/
│   ├── app.py            # all routes
│   ├── db.py             # models (User/Team/Challenge/Hint/Submission/Comment/Announcement/...)
│   ├── seeds.py          # 100 sample challenges
│   ├── docker_runner.py  # ephemeral container manager + reaper
│   └── requirements.txt
├── frontend/
│   └── src/{main.js, App.vue}
├── docs/
│   ├── API.md
│   └── 课程设计报告.md
├── docker-compose.yml
└── README.md
```

## ⌨️ Admin Quick Start

1. Login as `admin / admin123`
2. Click **🛠 管理后台** in the header
3. Tabs:
   - **比赛设置** — set contest name, start / end time
   - **发布公告** — broadcast announcements to all users
   - **新建题目** — create a challenge with dynamic score (base / min), category, difficulty, flag, description, and either:
     - **外部靶机 URL** (recommended): point to your own server's challenge
     - **Docker 镜像**: let the platform spin up an ephemeral container

## 📝 License

MIT — see [LICENSE](LICENSE).

---

# 中文说明

一个功能完整、可自托管的 CTF 训练 / 比赛平台，开箱自带 **100 道题**，支持动态分值、Docker 临时靶机、提示系统、讨论区、排行榜导出等比赛级功能。

## 功能列表

### 核心
- 用户注册 / 登录（JWT，密码哈希）
- 内置 **100 道 CTF 题**：Web / Misc / Crypto / Reverse 各 25 道
- Flag 在线提交自动判分，不重复计分
- 实时排行榜（前 50），CSV 导出

### 比赛规则
- 📈 **动态分值**：第一个做出来的人拿满分（默认 500），之后每多一人做出来分数递减，最低 100
- 🩸 **First / Second / Third Blood** 前三杀特别标记 + 庆祝提示
- 💡 **提示系统**：花积分买提示
- ⏳ **比赛倒计时**：可配置开始 / 结束时间，未开始 / 已结束自动锁题
- 📢 公告横幅
- 🛡 防作弊：同 IP 注册限制、Flag 提交频率限制（60 秒 5 次）

### 靶机
- 🐳 **一键拉起 Docker 临时靶机**：每人独立容器，30 分钟自动回收，可续期
- 🌐 **外部靶机 URL**：直接填你自己服务器的地址，选手点链接进，不用平台打包镜像
- 📎 题目附件上传 / 下载

### 协作
- 💬 每道题独立讨论区，自动拦截发 flag
- 📝 解出题目后可上传 WriteUp（.md / .pdf）
- 📊 个人解题雷达图（四类掌握程度）

### 管理员后台
- 新建 / 删除题目
- 配置动态分（起始分 / 最低分）
- 上传附件
- 发布公告
- 设置比赛时间窗
- 导出成绩 CSV

## 快速启动

```bash
# 本地
cd backend && pip install -r requirements.txt && python app.py
cd frontend && npm install && npm run dev

# Docker
docker compose up -d --build
# 前端 http://127.0.0.1:8080
```

演示账号：**admin / admin123**（管理员）

## 安全说明

本平台仅用于教学与合法比赛。Docker 容器资源受限（256MB 内存），退出自动销毁。
