"""
认证与权限装饰器
"""
import jwt
import datetime
from functools import wraps
from flask import request, current_app, g
from app.utils.responses import error_response


def generate_token(user_id: int, username: str, expires_hours: int = 24 * 7) -> str:
    """生成 JWT Token，默认 7 天有效期"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours),
        "iat": datetime.datetime.utcnow(),
    }
    secret = current_app.config["SECRET_KEY"]
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """解码 JWT Token"""
    secret = current_app.config["SECRET_KEY"]
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return {"error": "token_expired"}
    except jwt.InvalidTokenError:
        return {"error": "token_invalid"}


def login_required(f):
    """登录校验装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("未提供认证 Token", 401)
        token = auth_header[7:]
        payload = decode_token(token)
        if "error" in payload:
            return error_response("Token 无效或已过期，请重新登录", 401)
        g.current_user_id = payload["user_id"]
        g.current_username = payload["username"]
        return f(*args, **kwargs)
    return wrapper


def get_current_user_id() -> int:
    """获取当前登录用户 ID（用于多用户数据隔离）"""
    return getattr(g, "current_user_id", None)
