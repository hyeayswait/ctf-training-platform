# 🚩 CTF Training Platform

[![Vue3](https://img.shields.io/badge/frontend-Vue%203-42b883)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/backend-Flask-000000)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/deploy-Docker%20Compose-2496ed)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A lightweight, self-hosted CTF training platform for classes, clubs and skill contests.
Supports problem categories, flag submission with automatic judging, scoreboard,
and **one-click ephemeral Docker environments** for web challenges.

> 🎓 For educational use only. Run it on your own servers / in your own lab.

## ✨ Features

- 🔐 User register / login (JWT, hashed passwords)
- 👥 Team support (auto-create on registration)
- 📚 Challenge categories: Web / Misc / Crypto / Reverse / Pwn
- 🚩 Flag submission with auto-judging, anti-duplicate scoring
- 🏆 Live scoreboard (top 50)
- 🐳 **One-click Docker ephemeral environments** per user, auto-cleanup on exit
- 🎨 Dark hacker theme with Element Plus

## 🚀 Quick Start

```bash
# 1. 本地直跑
cd backend && pip install -r requirements.txt && python app.py   # :5000
cd frontend && npm install && npm run dev                       # :5173

# 2. 或 Docker Compose
docker compose up -d --build
# frontend http://127.0.0.1:8080
```

Demo account: `admin / admin123`

## 📂 Structure

```
ctf-platform/
├── backend/
│   ├── app.py          # Flask routes
│   ├── db.py           # SQLAlchemy models
│   ├── seeds.py        # sample challenges
│   ├── docker_runner.py # ephemeral container manager
│   └── requirements.txt
├── frontend/
│   └── src/{main.js, App.vue}
├── docker-compose.yml
└── docs/
```

## 📝 License

MIT — see [LICENSE](LICENSE).

---

# 中文说明

一个轻量、可自托管的 CTF 训练平台，适合课堂练习、社团训练和技能竞赛模拟。

## 功能

- 用户注册 / 登录（JWT，密码哈希存储）
- 战队支持（注册时填战队名自动创建）
- 题目分类：Web / Misc / Crypto / Reverse / Pwn
- Flag 提交自动判分，同一题不重复计分
- 实时排行榜（前 50 名）
- **一键拉起 Docker 临时靶机环境**，用户退出后自动销毁
- 暗色黑客风 UI

## 快速启动

```bash
# 后端
cd backend && pip install -r requirements.txt && python app.py

# 前端
cd frontend && npm install && npm run dev

# 或 Docker
docker compose up -d --build
```

演示账号：`admin / admin123`

## 安全说明

本平台仅用于教学与合法比赛。题目环境由 Docker 隔离，资源受限（CPU/内存上限），退出自动销毁。
