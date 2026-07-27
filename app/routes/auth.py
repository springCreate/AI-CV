"""
用户认证路由
"""
import datetime
from flask import Blueprint, request, g
from app.extensions import db
from app.models.user import User
from app.utils.decorators import generate_token, login_required
from app.utils.responses import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    nickname = (data.get("nickname") or "").strip()

    if not username or not password:
        return error_response("用户名和密码不能为空", 400)
    if len(username) < 3 or len(username) > 32:
        return error_response("用户名长度需为 3-32 位", 400)
    if len(password) < 6 or len(password) > 64:
        return error_response("密码长度需为 6-64 位", 400)

    if User.query.filter_by(username=username).first():
        return error_response("用户名已被注册", 409)

    user = User(
        username=username,
        nickname=nickname or username,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id, user.username)
    return success_response(
        data={"token": token, "user": user.to_dict()},
        message="注册成功",
        code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return error_response("用户名和密码不能为空", 400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error_response("用户名或密码错误", 401)

    user.last_login_at = datetime.datetime.utcnow()
    db.session.commit()

    token = generate_token(user.id, user.username)
    return success_response(
        data={"token": token, "user": user.to_dict()},
        message="登录成功",
    )


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    """获取当前登录用户信息"""
    user = User.query.get(g.current_user_id)
    if not user:
        return error_response("用户不存在", 404)
    return success_response(data=user.to_dict())


@auth_bp.route("/me", methods=["PUT"])
@login_required
def update_me():
    """更新当前用户基础信息"""
    user = User.query.get(g.current_user_id)
    if not user:
        return error_response("用户不存在", 404)

    data = request.get_json() or {}
    for field in ["nickname", "email", "phone", "target_position", "target_city"]:
        if field in data:
            setattr(user, field, data[field])
    if "expected_salary_min" in data:
        try:
            user.expected_salary_min = int(data["expected_salary_min"]) if data["expected_salary_min"] else None
        except (ValueError, TypeError):
            return error_response("期望薪资需为整数", 400)

    db.session.commit()
    return success_response(data=user.to_dict(), message="信息更新成功")


@auth_bp.route("/password", methods=["PUT"])
@login_required
def reset_password():
    """重置密码"""
    user = User.query.get(g.current_user_id)
    if not user:
        return error_response("用户不存在", 404)

    data = request.get_json() or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""

    if not user.check_password(old_password):
        return error_response("原密码错误", 400)
    if len(new_password) < 6 or len(new_password) > 64:
        return error_response("新密码长度需为 6-64 位", 400)

    user.set_password(new_password)
    db.session.commit()
    return success_response(message="密码重置成功")
