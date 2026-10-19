"""
Docker 环境拉起模块：
- 用 docker SDK 为当前用户启动一个临时靶题容器
- 记录容器 ID，方便后续关闭
- 没装 docker / SDK 不可用时降级为返回一个"环境不可用，请联系管理员"的提示
"""
import os
import threading
import atexit

try:
    import docker  # type: ignore
    _client = docker.from_env()
    _client.ping()
    _HAS_DOCKER = True
except Exception:
    _client = None
    _HAS_DOCKER = False

# user_id -> {"container_id": ..., "url": ...}
_active = {}
_lock = threading.Lock()


def docker_available() -> bool:
    return _HAS_DOCKER


def start_env(user_id: int, image: str, internal_port: int) -> dict:
    """为指定用户拉起一个容器。返回 {url, container_id}"""
    if not _HAS_DOCKER:
        return {"url": "", "container_id": "",
                "message": "本环境未启用 Docker 沙箱，请联系管理员手动提供靶机地址。"}

    with _lock:
        # 该用户已经有在跑的容器，直接复用
        if user_id in _active:
            return _active[user_id]

        # 随机选一个高位端口
        import socket
        s = socket.socket()
        s.bind(("0.0.0.0", 0))
        host_port = s.getsockname()[1]
        s.close()

        try:
            container = _client.containers.run(
                image,
                detach=True,
                ports={f"{internal_port}/tcp": host_port},
                mem_limit="256m",
                cpu_quota=50000,
            )
        except Exception as e:
            return {"url": "", "container_id": "",
                    "message": f"容器启动失败：{e}"}

        info = {
            "url": f"http://127.0.0.1:{host_port}",
            "container_id": container.id,
        }
        _active[user_id] = info
        return info


def stop_env(user_id: int) -> bool:
    with _lock:
        info = _active.pop(user_id, None)
    if not info or not _HAS_DOCKER:
        return False
    try:
        c = _client.containers.get(info["container_id"])
        c.stop(timeout=3)
        c.remove()
        return True
    except Exception:
        return False


def _cleanup_all():
    """退出时把所有拉起的容器清理掉"""
    if not _HAS_DOCKER:
        return
    for uid in list(_active.keys()):
        stop_env(uid)


atexit.register(_cleanup_all)
