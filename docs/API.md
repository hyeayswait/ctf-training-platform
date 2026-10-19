# 接口文档

Base URL: `http://127.0.0.1:5000/api`

除 `auth/register`、`auth/login`、`scoreboard` 外，均需 `Authorization: Bearer <token>`。

| Method | Path | 说明 |
| --- | --- | --- |
| POST | /auth/register | 注册，body: username/password/team? |
| POST | /auth/login | 登录，返回 token |
| GET | /challenges | 题目列表（含 solved 标记） |
| GET | /challenges/{id} | 题目详情（含描述） |
| POST | /submit | 提交 flag，body: challenge_id/flag |
| GET | /scoreboard | 排行榜（前 50） |
| POST | /env/start/{cid} | 拉起该题的 Docker 环境 |
| POST | /env/stop/{cid} | 关闭当前用户的环境 |
