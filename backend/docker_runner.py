"""Docker 环境管理：拉起临时容器 + 30 分钟自动回收。"""
import threading
import time
from datetime import datetime, timedelta

try:
    import docker  # type: ignore
    _client = docker.from_env()
    _client.ping()
    _HAS_DOCKER = True
except Exception:
    _client = None
    _HAS_DOCKER = False

# user_id -> {"container_id", "url", "start_time", "expires_at"}
_active = {}
_lock = threading.Lock()
TTL = 30 * 60   # 30 分钟自动回收


def docker_available():
    return _HAS_DOCKER


def start_env(user_id, image, internal_port):
    if not _HAS_DOCKER:
        return {"url": "", "container_id": "",
                "message": "本环境未启用 Docker 沙箱，请联系管理员。"}
    with _lock:
        if user_id in _active:
            return _active[user_id]
        import socket
        s = socket.socket(); s.bind(("0.0.0.0", 0)); host_port = s.getsockname()[1]; s.close()
        try:
            c = _client.containers.run(image, detach=True,
                                       ports={f"{internal_port}/tcp": host_port},
                                       mem_limit="256m", cpu_quota=50000)
        except Exception as e:
            return {"url": "", "container_id": "", "message": f"容器启动失败：{e}"}
        now = datetime.now()
        info = {"url": f"http://127.0.0.1:{host_port}", "container_id": c.id,
                "start_time": now, "expires_at": now + timedelta(seconds=TTL)}
        _active[user_id] = info
        return info


def stop_env(user_id):
    with _lock:
        info = _active.pop(user_id, None)
    if not info or not _HAS_DOCKER:
        return False
    try:
        c = _client.containers.get(info["container_id"])
        c.stop(timeout=3); c.remove()
        return True
    except Exception:
        return False


def renew_env(user_id):
    """续期 30 分钟"""
    with _lock:
        if user_id in _active:
            _active[user_id]["expires_at"] = datetime.now() + timedelta(seconds=TTL)
            return True
    return False


def _reaper():
    """后台线程：每 60 秒扫一次，关掉过期容器"""
    while True:
        time.sleep(60)
        now = datetime.now()
        expired = []
        with _lock:
            for uid, info in list(_active.items()):
                if now > info["expires_at"]:
                    expired.append(uid)
        for uid in expired:
            stop_env(uid)
            try:
                from flask import current_app
                # 仅在 app 上下文里打印日志
            except Exception:
                pass


threading.Thread(target=_reaper, daemon=True).start()
