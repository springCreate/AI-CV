"""
统一 API 响应格式
"""
from flask import jsonify


def success_response(data=None, message="操作成功", code=200, **extra):
    """成功响应"""
    resp = {
        "code": code,
        "success": True,
        "message": message,
        "data": data,
    }
    if extra:
        resp["data"] = resp["data"] or {}
        resp["data"].update(extra)
    return jsonify(resp), code


def error_response(message="操作失败", code=400, data=None):
    """错误响应"""
    resp = {
        "code": code,
        "success": False,
        "message": message,
        "data": data,
    }
    return jsonify(resp), code


def paginate_response(query, page, per_page, schema=None):
    """分页响应封装

    schema 支持两种形式：
    - Marshmallow Schema 对象：调用 schema.dump(item)
    - 普通可调用对象：调用 schema(item)
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items
    if schema:
        if hasattr(schema, "dump"):
            items = [schema.dump(item) for item in items]
        else:
            items = [schema(item) for item in items]
    return success_response({
        "items": items,
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    })
