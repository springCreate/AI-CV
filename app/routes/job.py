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


@job_bp.route("", methods=["POST"])
@login_required
def create_job():
    """
    手动录入真实岗位
    请求体：{
        "title": "岗位名称",
        "company": "公司名称",
        "city": "城市",
        "salary_min": 10000,
        "salary_max": 20000,
        "work_years": "1-3年",
        "education": "本科",
        "jd_text": "岗位职责...",
        "job_url": "https://www.zhipin.com/job_detail/...",
        "company_size": "1000-5000人",
        "company_industry": "互联网",
        "job_type": "全职",
        "is_weekend_off": true,
        "has_accommodation": false
    }
    """
    data = request.get_json() or {}
    required_fields = ["title", "company", "job_url"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return error_response(f"缺少必填字段: {', '.join(missing)}", 400)

    job = Job(
        user_id=g.current_user_id,
        platform="manual",
        platform_job_id=f"manual_{datetime.datetime.utcnow().timestamp()}",
        title=data.get("title", "").strip(),
        company=data.get("company", "").strip(),
        city=data.get("city", "").strip(),
        district=data.get("district", "").strip(),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        salary_text=data.get("salary_text", ""),
        work_years=data.get("work_years", ""),
        education=data.get("education", ""),
        job_type=data.get("job_type", "全职"),
        is_weekend_off=data.get("is_weekend_off"),
        has_accommodation=data.get("has_accommodation"),
        jd_text=data.get("jd_text", ""),
        company_size=data.get("company_size", ""),
        company_industry=data.get("company_industry", ""),
        hr_name=data.get("hr_name", ""),
        job_url=data.get("job_url", "").strip(),
        last_fetched_at=datetime.datetime.utcnow(),
    )
    db.session.add(job)
    db.session.commit()
    return success_response(data=job.to_dict(), message="岗位录入成功", code=201)


# ============ 智能匹配 ============

@job_bp.route("/match", methods=["POST"])
@login_required
def match_single_job():
    """
    单岗位智能匹配（选择简历+岗位+模板）
    请求体：
    {
        "resume_id": 1,
        "job_id": 1,
        "template_id": 1
    }
    """
    data = request.get_json() or {}
    resume_id = data.get("resume_id")
    job_id = data.get("job_id")
    template_id = data.get("template_id")

    if not resume_id or not job_id or not template_id:
        return error_response("请提供 resume_id、job_id 和 template_id", 400)

    resume = Resume.query.filter_by(id=resume_id, user_id=g.current_user_id).first()
    if not resume:
        return error_response("简历不存在", 404)

    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return error_response("岗位不存在", 404)

    template = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()
    if not template:
        return error_response("求职诉求模板不存在", 404)

    try:
        result = JobMatcher.match_single_job(g.current_user_id, resume, job, template)
    except Exception as e:
        current_app.logger.exception("单岗位匹配失败")
        return error_response(f"匹配失败: {e}", 500)

    return success_response(data=result, message=f"匹配完成，得分 {result['match_score']}")


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
    """获取数据源状态（当前仅支持 Mock 演示数据 + 手动录入）"""
    cfg = current_app.config.get("JOB_PLATFORMS_CFG", {})
    return success_response(data={
        "platforms": [
            {"platform": "mock", "enabled": cfg.get("mock_mode", True)},
            {"platform": "manual", "enabled": True},
        ],
        "mock_mode": cfg.get("mock_mode", True),
        "active_count": 0,
    })
