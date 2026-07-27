"""
面试题库路由
"""
from flask import Blueprint, request, g, current_app
from sqlalchemy import desc

from app.extensions import db
from app.models.resume import Resume
from app.models.job import Job
from app.models.interview import InterviewQuestion
from app.services.interview_service import InterviewService
from app.utils.decorators import login_required
from app.utils.responses import success_response, error_response, paginate_response

interview_bp = Blueprint("interview", __name__)


@interview_bp.route("", methods=["GET"])
@login_required
def list_questions():
    """面试问题列表"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    job_id = request.args.get("job_id", type=int)

    query = InterviewQuestion.query.filter_by(user_id=g.current_user_id)
    if job_id:
        query = query.filter(InterviewQuestion.job_id == job_id)

    query = query.order_by(desc(InterviewQuestion.created_at))
    return paginate_response(query, page, per_page, schema=lambda item: item.to_dict())


@interview_bp.route("/<int:q_id>", methods=["GET"])
@login_required
def get_question(q_id: int):
    q = InterviewQuestion.query.filter_by(id=q_id, user_id=g.current_user_id).first()
    if not q:
        return error_response("问题不存在", 404)
    return success_response(data=q.to_dict())


@interview_bp.route("/<int:q_id>", methods=["DELETE"])
@login_required
def delete_question(q_id: int):
    q = InterviewQuestion.query.filter_by(id=q_id, user_id=g.current_user_id).first()
    if not q:
        return error_response("问题不存在", 404)
    db.session.delete(q)
    db.session.commit()
    return success_response(message="已删除")


@interview_bp.route("/generate", methods=["POST"])
@login_required
def generate_questions():
    """
    根据岗位JD和简历生成面试题
    请求体：{"resume_id": 1, "job_id": 1}
    """
    data = request.get_json() or {}
    resume_id = data.get("resume_id")
    job_id = data.get("job_id")

    if not resume_id or not job_id:
        return error_response("请提供 resume_id 和 job_id", 400)

    resume = Resume.query.filter_by(id=resume_id, user_id=g.current_user_id).first()
    if not resume:
        return error_response("简历不存在", 404)

    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return error_response("岗位不存在", 404)

    try:
        questions = InterviewService.generate_questions(resume, job)
        saved_count = InterviewService.save_questions(g.current_user_id, resume_id, job_id, questions)
    except Exception as e:
        current_app.logger.exception("面试题生成失败")
        return error_response(f"面试题生成失败: {e}", 500)

    return success_response(data={
        "questions": questions,
        "saved_count": saved_count,
    }, message=f"成功生成 {len(questions)} 道面试题")
