"""
求职诉求模板管理路由
"""
from flask import Blueprint, request, g
from app.extensions import db
from app.models.template import JobTemplate
from app.utils.decorators import login_required
from app.utils.responses import success_response, error_response

template_bp = Blueprint("template", __name__)


def _serialize_template_fields(data: dict) -> dict:
    """把前端字段映射到模型字段（处理 list -> str）"""
    fields = {}
    list_fields = ["cities", "keywords"]
    for k, v in data.items():
        if k in list_fields and isinstance(v, list):
            fields[k] = ",".join(str(x).strip() for x in v if x)
        else:
            fields[k] = v
    return fields


@template_bp.route("", methods=["GET"])
@login_required
def list_templates():
    """获取当前用户所有诉求模板"""
    items = JobTemplate.query.filter_by(user_id=g.current_user_id).order_by(
        JobTemplate.is_default.desc(), JobTemplate.updated_at.desc()
    ).all()
    return success_response(data=[t.to_dict() for t in items])


@template_bp.route("/<int:template_id>", methods=["GET"])
@login_required
def get_template(template_id: int):
    t = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()
    if not t:
        return error_response("模板不存在", 404)
    return success_response(data=t.to_dict())


@template_bp.route("", methods=["POST"])
@login_required
def create_template():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error_response("模板名称不能为空", 400)

    fields = _serialize_template_fields(data)
    t = JobTemplate(user_id=g.current_user_id, name=name)
    for k, v in fields.items():
        if k == "name":
            continue
        if k in ["is_default", "require_weekend_off", "require_no_overtime",
                 "require_accommodation", "intern_certificate"]:
            setattr(t, k, bool(v))
        elif k in ["salary_min", "salary_max", "work_years_min", "work_years_max",
                   "intern_min_months"]:
            try:
                setattr(t, k, int(v) if v not in (None, "") else None)
            except (ValueError, TypeError):
                pass
        else:
            setattr(t, k, v)

    # 若设为默认，取消其他默认
    if t.is_default:
        JobTemplate.query.filter_by(user_id=g.current_user_id, is_default=True).update(
            {"is_default": False}
        )

    db.session.add(t)
    db.session.commit()
    return success_response(data=t.to_dict(), message="模板创建成功", code=201)


@template_bp.route("/<int:template_id>", methods=["PUT"])
@login_required
def update_template(template_id: int):
    t = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()
    if not t:
        return error_response("模板不存在", 404)

    data = request.get_json() or {}
    fields = _serialize_template_fields(data)

    for k, v in fields.items():
        if k == "id" or k == "user_id":
            continue
        if k in ["is_default", "require_weekend_off", "require_no_overtime",
                 "require_accommodation", "intern_certificate"]:
            setattr(t, k, bool(v))
        elif k in ["salary_min", "salary_max", "work_years_min", "work_years_max",
                   "intern_min_months"]:
            try:
                setattr(t, k, int(v) if v not in (None, "") else None)
            except (ValueError, TypeError):
                pass
        else:
            setattr(t, k, v)

    if t.is_default:
        JobTemplate.query.filter(
            JobTemplate.user_id == g.current_user_id,
            JobTemplate.is_default == True,
            JobTemplate.id != t.id,
        ).update({"is_default": False})

    db.session.commit()
    return success_response(data=t.to_dict(), message="更新成功")


@template_bp.route("/<int:template_id>", methods=["DELETE"])
@login_required
def delete_template(template_id: int):
    t = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()
    if not t:
        return error_response("模板不存在", 404)
    db.session.delete(t)
    db.session.commit()
    return success_response(message="删除成功")


@template_bp.route("/<int:template_id>/set-default", methods=["POST"])
@login_required
def set_default(template_id: int):
    """设为默认模板"""
    t = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()
    if not t:
        return error_response("模板不存在", 404)
    JobTemplate.query.filter_by(user_id=g.current_user_id, is_default=True).update(
        {"is_default": False}
    )
    t.is_default = True
    db.session.commit()
    return success_response(message="已设为默认模板")
