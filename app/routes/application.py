"""
投递辅助路由

包含：
- 投递记录 CRUD
- AI 话术生成（单岗位/批量）
- Excel 清单导出
- 投递去重管理
- 投递统计
"""
import os
import datetime
from flask import Blueprint, request, g, send_file, current_app
from sqlalchemy import or_

from app.extensions import db
from app.models.resume import Resume
from app.models.job import Job, JobMatchRecord
from app.models.application import ApplicationRecord
from app.services.application_assistant import ApplicationAssistant
from app.services.excel_export import ExcelExporter
from app.utils.decorators import login_required
from app.utils.responses import success_response, error_response, paginate_response

application_bp = Blueprint("application", __name__)


# ============ 投递记录管理 ============

@application_bp.route("", methods=["GET"])
@login_required
def list_applications():
    """投递记录列表"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    status = request.args.get("status")
    company = request.args.get("company")

    query = ApplicationRecord.query.filter_by(user_id=g.current_user_id)
    if status:
        query = query.filter(ApplicationRecord.status == status)
    if company:
        query = query.join(Job).filter(Job.company.contains(company))

    query = query.order_by(ApplicationRecord.updated_at.desc())
    return paginate_response(query, page, per_page, schema=lambda item: item.to_dict())


@application_bp.route("/<int:app_id>", methods=["GET"])
@login_required
def get_application(app_id: int):
    app = ApplicationRecord.query.filter_by(id=app_id, user_id=g.current_user_id).first()
    if not app:
        return error_response("记录不存在", 404)
    return success_response(data=app.to_dict())


@application_bp.route("", methods=["POST"])
@login_required
def create_application():
    """
    手动创建投递记录（用于已通过外部投递的岗位补录）
    请求体：{"job_id": 1, "resume_id": 1, "status": "applied", "remark": "..."}
    """
    data = request.get_json() or {}
    job_id = data.get("job_id")
    if not job_id:
        return error_response("请提供 job_id", 400)

    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return error_response("岗位不存在", 404)

    # 投递去重：同一岗位只能有一条投递记录
    existing = ApplicationRecord.query.filter_by(
        user_id=g.current_user_id, job_id=job_id
    ).first()
    if existing:
        return error_response(f"该岗位已有投递记录（状态：{existing.status}）", 409)

    app = ApplicationRecord(
        user_id=g.current_user_id,
        job_id=job_id,
        resume_id=data.get("resume_id"),
        status=data.get("status", "applied"),
        applied_via=data.get("applied_via", "外部"),
        remark=data.get("remark", ""),
    )
    if app.status in ("applied", "interview", "offer"):
        app.applied_at = datetime.datetime.utcnow()

    db.session.add(app)
    db.session.commit()
    return success_response(data=app.to_dict(), message="投递记录已创建", code=201)


@application_bp.route("/<int:app_id>", methods=["PUT"])
@login_required
def update_application(app_id: int):
    """更新投递状态/备注"""
    app = ApplicationRecord.query.filter_by(id=app_id, user_id=g.current_user_id).first()
    if not app:
        return error_response("记录不存在", 404)

    data = request.get_json() or {}
    if "status" in data:
        app.status = data["status"]
        # 状态变为 applied 时记录投递时间
        if data["status"] in ("applied", "interview", "offer") and not app.applied_at:
            app.applied_at = datetime.datetime.utcnow()
    if "remark" in data:
        app.remark = data["remark"]

    db.session.commit()
    return success_response(data=app.to_dict(), message="更新成功")


@application_bp.route("/<int:app_id>", methods=["DELETE"])
@login_required
def delete_application(app_id: int):
    app = ApplicationRecord.query.filter_by(id=app_id, user_id=g.current_user_id).first()
    if not app:
        return error_response("记录不存在", 404)
    db.session.delete(app)
    db.session.commit()
    return success_response(message="已删除")


@application_bp.route("/<int:app_id>/mark-applied", methods=["POST"])
@login_required
def mark_applied(app_id: int):
    """快捷标记为已投递"""
    app = ApplicationRecord.query.filter_by(id=app_id, user_id=g.current_user_id).first()
    if not app:
        return error_response("记录不存在", 404)
    app.status = "applied"
    app.applied_at = datetime.datetime.utcnow()
    db.session.commit()
    return success_response(message="已标记为已投递")


# ============ AI 话术生成 ============

@application_bp.route("/<int:job_id>/generate-script", methods=["POST"])
@login_required
def generate_script(job_id: int):
    """
    为单个岗位生成 AI 定制话术
    请求体：{"resume_id": 1, "save": true}
    """
    data = request.get_json() or {}
    resume_id = data.get("resume_id")
    save = data.get("save", True)

    if not resume_id:
        return error_response("请提供 resume_id", 400)

    resume = Resume.query.filter_by(id=resume_id, user_id=g.current_user_id).first()
    if not resume:
        return error_response("简历不存在", 404)

    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return error_response("岗位不存在", 404)

    try:
        content = ApplicationAssistant.generate_greeting_and_intro(resume, job)
    except Exception as e:
        current_app.logger.exception("话术生成失败")
        return error_response(f"AI 话术生成失败: {e}", 500)

    if save:
        # 找已有投递记录或创建
        app = ApplicationRecord.query.filter_by(
            user_id=g.current_user_id, job_id=job_id
        ).first()
        if not app:
            app = ApplicationRecord(
                user_id=g.current_user_id,
                job_id=job_id,
                resume_id=resume_id,
                status="not_applied",
            )
            db.session.add(app)
        app.greeting_message = content["greeting"]
        app.self_introduction = content["self_introduction"]
        db.session.commit()
        return success_response(data={"application": app.to_dict(), "content": content},
                                message="话术已生成并保存")
    return success_response(data={"content": content}, message="话术已生成")


@application_bp.route("/batch-generate-scripts", methods=["POST"])
@login_required
def batch_generate_scripts():
    """
    批量生成话术
    请求体：{"resume_id": 1, "job_ids": [1, 2, 3]}
    """
    data = request.get_json() or {}
    resume_id = data.get("resume_id")
    job_ids = data.get("job_ids", [])

    # 兼容前端字符串/数组输入
    if isinstance(job_ids, str):
        job_ids = [x.strip() for x in job_ids.replace('，', ',').split(',') if x.strip()]
    job_ids = [int(x) for x in job_ids if x]

    if not resume_id or not job_ids:
        return error_response("请提供 resume_id 和 job_ids", 400)

    resume = Resume.query.filter_by(id=resume_id, user_id=g.current_user_id).first()
    if not resume:
        return error_response("简历不存在", 404)

    jobs = Job.query.filter(
        Job.id.in_(job_ids),
        Job.user_id == g.current_user_id,
    ).all()

    if not jobs:
        return error_response("未找到符合条件的岗位", 404)

    results = ApplicationAssistant.batch_generate(resume, jobs)

    # 保存到投递记录
    saved = 0
    for r in results:
        if not r["success"]:
            continue
        app = ApplicationRecord.query.filter_by(
            user_id=g.current_user_id, job_id=r["job_id"]
        ).first()
        if not app:
            app = ApplicationRecord(
                user_id=g.current_user_id,
                job_id=r["job_id"],
                resume_id=resume_id,
                status="not_applied",
            )
            db.session.add(app)
        app.greeting_message = r["greeting"]
        app.self_introduction = r["self_introduction"]
        saved += 1
    db.session.commit()

    return success_response(data={
        "total": len(jobs),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "saved": saved,
        "items": results,
    }, message=f"批量生成完成，成功 {sum(1 for r in results if r['success'])}/{len(jobs)}")


# ============ Excel 导出 ============

@application_bp.route("/export-excel", methods=["POST"])
@login_required
def export_excel():
    """
    导出匹配清单为 Excel
    请求体：
    {
        "template_id": 1,           # 可选，按模板筛选
        "job_ids": [1, 2, 3],       # 可选，指定岗位
        "min_score": 60,            # 可选，最低匹配分数
        "only_unapplied": true      # 可选，仅未投递
    }
    """
    data = request.get_json() or {}
    template_id = data.get("template_id")
    job_ids = data.get("job_ids")
    min_score = data.get("min_score", 0)
    only_unapplied = data.get("only_unapplied", False)

    if isinstance(job_ids, str):
        job_ids = [x.strip() for x in job_ids.replace('，', ',').split(',') if x.strip()]
    if job_ids:
        job_ids = [int(x) for x in job_ids]

    query = JobMatchRecord.query.filter_by(
        user_id=g.current_user_id,
        hard_filter_passed=True,
    )
    if template_id:
        query = query.filter(JobMatchRecord.template_id == template_id)
    if job_ids:
        query = query.filter(JobMatchRecord.job_id.in_(job_ids))
    if min_score:
        query = query.filter(JobMatchRecord.match_score >= min_score)

    records = query.all()

    if only_unapplied:
        records = [r for r in records if not ApplicationRecord.query.filter_by(
            user_id=g.current_user_id, job_id=r.job_id,
            status="applied"
        ).first()]

    if not records:
        return error_response("没有符合条件的岗位可导出", 400)

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"岗位匹配清单_{timestamp}.xlsx"
        file_path = ExcelExporter.export_match_list(records, filename)
    except Exception as e:
        current_app.logger.exception("Excel 导出失败")
        return error_response(f"Excel 导出失败: {e}", 500)

    return success_response(
        data={
            "file_path": file_path,
            "download_url": f"/api/application/download-excel?path={file_path}",
            "record_count": len(records),
        },
        message=f"已导出 {len(records)} 条记录",
    )


@application_bp.route("/download-excel", methods=["GET"])
@login_required
def download_excel():
    """下载 Excel 文件"""
    file_path = request.args.get("path", "")
    if not file_path or not os.path.exists(file_path):
        return error_response("文件不存在", 404)

    # 安全检查：确保文件在导出目录内
    from flask import current_app
    export_dir = os.path.abspath(os.path.join(
        current_app.config["BASE_DIR"],
        current_app.config["STORAGE_CFG"]["export_dir"]
    ))
    if not os.path.abspath(file_path).startswith(export_dir):
        return error_response("无权访问该文件", 403)

    filename = os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)


# ============ 投递统计 ============

@application_bp.route("/stats", methods=["GET"])
@login_required
def application_stats():
    """投递统计"""
    user_id = g.current_user_id
    total = ApplicationRecord.query.filter_by(user_id=user_id).count()
    applied = ApplicationRecord.query.filter_by(user_id=user_id, status="applied").count()
    interviewing = ApplicationRecord.query.filter_by(user_id=user_id, status="interview").count()
    offered = ApplicationRecord.query.filter_by(user_id=user_id, status="offer").count()
    rejected = ApplicationRecord.query.filter_by(user_id=user_id, status="rejected").count()
    not_applied = ApplicationRecord.query.filter_by(user_id=user_id, status="not_applied").count()

    # 近 7 日投递趋势
    trend = []
    for i in range(6, -1, -1):
        day = datetime.datetime.utcnow().date() - datetime.timedelta(days=i)
        day_start = datetime.datetime.combine(day, datetime.time.min)
        day_end = datetime.datetime.combine(day, datetime.time.max)
        count = ApplicationRecord.query.filter(
            ApplicationRecord.user_id == user_id,
            ApplicationRecord.applied_at.between(day_start, day_end),
        ).count()
        trend.append({"date": day.isoformat(), "count": count})

    return success_response(data={
        "total": total,
        "applied": applied,
        "interviewing": interviewing,
        "offered": offered,
        "rejected": rejected,
        "not_applied": not_applied,
        "trend_7d": trend,
    })
