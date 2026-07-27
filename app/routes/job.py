"""
岗位管理路由

包含：
- 岗位列表查询、详情
- 一键拉取 + 匹配
- 黑名单管理
- 匹配记录查询
- 新岗位提醒
"""
import datetime
from flask import Blueprint, request, g, current_app
from sqlalchemy import or_, and_, desc

from app.extensions import db
from app.models.resume import Resume
from app.models.template import JobTemplate
from app.models.job import Job, JobMatchRecord, Blacklist, JobRefreshLog
from app.models.application import ApplicationRecord
from app.services.job_matcher import JobMatcher
from app.services.job_platform import PlatformManager
from app.utils.decorators import login_required
from app.utils.responses import success_response, error_response, paginate_response

job_bp = Blueprint("job", __name__)


# ============ 岗位查询 ============

@job_bp.route("", methods=["GET"])
@login_required
def list_jobs():
    """岗位列表（支持筛选）"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    platform = request.args.get("platform")
    city = request.args.get("city")
    keyword = request.args.get("keyword")
    min_score = request.args.get("min_score", type=int)
    only_passed = request.args.get("only_passed", "false").lower() == "true"

    query = Job.query.filter_by(user_id=g.current_user_id)

    if platform:
        query = query.filter(Job.platform == platform)
    if city:
        query = query.filter(Job.city.contains(city))
    if keyword:
        query = query.filter(or_(
            Job.title.contains(keyword),
            Job.company.contains(keyword),
        ))

    query = query.order_by(Job.last_fetched_at.desc())
    return paginate_response(query, page, per_page, schema=lambda item: item.to_dict())


@job_bp.route("/<int:job_id>", methods=["GET"])
@login_required
def get_job(job_id: int):
    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return error_response("岗位不存在", 404)
    return success_response(data=job.to_dict())


@job_bp.route("/<int:job_id>", methods=["DELETE"])
@login_required
def delete_job(job_id: int):
    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return error_response("岗位不存在", 404)
    db.session.delete(job)
    db.session.commit()
    return success_response(message="已删除")


# ============ 拉取与匹配 ============

@job_bp.route("/fetch-match", methods=["POST"])
@login_required
def fetch_and_match():
    """
    一键拉取岗位并匹配打分
    请求体：
    {
        "resume_id": 1,
        "template_id": 1,
        "keyword": "软件测试",   # 可选，默认用模板的 position
        "city": "北京"          # 可选，默认用模板的第一个城市
    }
    """
    data = request.get_json() or {}
    resume_id = data.get("resume_id")
    template_id = data.get("template_id")
    keyword = data.get("keyword", "")
    city = data.get("city", "")

    if not resume_id or not template_id:
        return error_response("请提供 resume_id 和 template_id", 400)

    resume = Resume.query.filter_by(id=resume_id, user_id=g.current_user_id).first()
    if not resume:
        return error_response("简历不存在", 404)

    template = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()
    if not template:
        return error_response("求职诉求模板不存在", 404)

    try:
        result = JobMatcher.fetch_and_match(
            g.current_user_id, resume, template, keyword, city
        )
    except Exception as e:
        current_app.logger.exception("岗位拉取匹配失败")
        return error_response(f"拉取匹配失败: {e}", 500)

    # 记录刷新日志
    log = JobRefreshLog(
        user_id=g.current_user_id,
        new_job_count=result["new_saved"],
        high_match_count=result["high_match_count"],
        status="success",
        finished_at=datetime.datetime.utcnow(),
    )
    db.session.add(log)
    db.session.commit()

    return success_response(data=result, message=f"拉取 {result['total_fetched']} 个岗位，新增 {result['new_saved']}，高匹配 {result['high_match_count']}")


@job_bp.route("/match-records", methods=["GET"])
@login_required
def list_match_records():
    """匹配记录列表"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    only_passed = request.args.get("only_passed", "true").lower() == "true"
    min_score = request.args.get("min_score", type=int)
    template_id = request.args.get("template_id", type=int)

    query = JobMatchRecord.query.filter_by(user_id=g.current_user_id)
    if only_passed:
        query = query.filter(JobMatchRecord.hard_filter_passed == True)
    if min_score is not None:
        query = query.filter(JobMatchRecord.match_score >= min_score)
    if template_id:
        query = query.filter(JobMatchRecord.template_id == template_id)

    query = query.order_by(JobMatchRecord.match_score.desc(), JobMatchRecord.created_at.desc())
    return paginate_response(query, page, per_page, schema=lambda item: item.to_dict())


@job_bp.route("/new-reminders", methods=["GET"])
@login_required
def new_reminders():
    """获取未读的新高匹配岗位提醒"""
    threshold = current_app.config.get("JOB_REFRESH_CFG", {}).get("high_match_threshold", 80)
    records = JobMatchRecord.query.filter_by(
        user_id=g.current_user_id,
        is_new=True,
        notified=False,
        hard_filter_passed=True,
    ).filter(JobMatchRecord.match_score >= threshold).all()

    # 标记为已通知
    for r in records:
        r.notified = True
    db.session.commit()

    return success_response(data={
        "count": len(records),
        "threshold": threshold,
        "items": [r.to_dict() for r in records[:20]],
    })


@job_bp.route("/<int:record_id>/mark-read", methods=["POST"])
@login_required
def mark_record_read(record_id: int):
    """标记匹配记录为已读"""
    r = JobMatchRecord.query.filter_by(id=record_id, user_id=g.current_user_id).first()
    if not r:
        return error_response("记录不存在", 404)
    r.is_new = False
    db.session.commit()
    return success_response(message="已标记为已读")


# ============ 黑名单管理 ============

@job_bp.route("/blacklist", methods=["GET"])
@login_required
def list_blacklist():
    items = Blacklist.query.filter_by(user_id=g.current_user_id).order_by(Blacklist.created_at.desc()).all()
    return success_response(data=[b.to_dict() for b in items])


@job_bp.route("/blacklist", methods=["POST"])
@login_required
def add_blacklist():
    data = request.get_json() or {}
    company = (data.get("company") or "").strip()
    if not company:
        return error_response("公司名称不能为空", 400)

    existing = Blacklist.query.filter_by(user_id=g.current_user_id, company=company).first()
    if existing:
        return error_response("该公司已在黑名单中", 409)

    b = Blacklist(
        user_id=g.current_user_id,
        company=company,
        reason=data.get("reason", ""),
    )
    db.session.add(b)
    db.session.commit()
    return success_response(data=b.to_dict(), message="已加入黑名单", code=201)


@job_bp.route("/blacklist/<int:blacklist_id>", methods=["DELETE"])
@login_required
def remove_blacklist(blacklist_id: int):
    b = Blacklist.query.filter_by(id=blacklist_id, user_id=g.current_user_id).first()
    if not b:
        return error_response("记录不存在", 404)
    db.session.delete(b)
    db.session.commit()
    return success_response(message="已移出黑名单")


# ============ 平台状态 ============

@job_bp.route("/platforms/status", methods=["GET"])
@login_required
def platforms_status():
    """获取各平台启用状态"""
    cfg = current_app.config["JOB_PLATFORMS_CFG"]
    manager = PlatformManager(cfg)
    data = []
    for name, adapter in manager.adapters.items():
        data.append({
            "platform": name,
            "enabled": adapter.is_available(),
        })
    data.append({
        "platform": "mock",
        "enabled": manager.is_mock_mode(),
    })
    return success_response(data={
        "platforms": data,
        "mock_mode": manager.is_mock_mode(),
        "active_count": sum(1 for a in manager.adapters.values() if a.is_available()),
    })
