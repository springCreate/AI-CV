"""
简历管理路由

包含：
- 文件上传与解析
- 简历 CRUD
- 子模块（教育/工作/项目/技能）增删改
- AI 优化（生成建议 + 应用建议）
- PDF 导出
"""
import os
import uuid
import logging
from pathlib import Path
from flask import Blueprint, request, g, send_file, current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.resume import (
    Resume, ResumeEducation, ResumeExperience,
    ResumeProject, ResumeSkill, ResumeOptimizationLog
)
from app.models.template import JobTemplate
from app.services.resume_parser import ResumeParser
from app.services.resume_optimizer import ResumeOptimizer
from app.services.pdf_generator import ResumePDFGenerator
from app.utils.decorators import login_required
from app.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)
resume_bp = Blueprint("resume", __name__)


def _get_user_resume(resume_id: int, user_id: int) -> Resume:
    """获取属于指定用户的简历（多用户隔离）"""
    r = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
    if not r:
        raise ValueError("简历不存在或无权访问")
    return r


def _save_upload(file) -> tuple:
    """保存上传文件，返回 (file_path, file_type, original_name)"""
    storage_cfg = current_app.config["STORAGE_CFG"]
    resume_dir = Path(current_app.config["BASE_DIR"]) / storage_cfg["resume_dir"]
    resume_dir.mkdir(parents=True, exist_ok=True)

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in ("pdf", "docx", "doc"):
        raise ValueError("仅支持 PDF 或 Word 文件")

    saved_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = resume_dir / saved_name
    file.save(str(file_path))
    return str(file_path), ext, original_name


# ============ 简历 CRUD ============

@resume_bp.route("", methods=["GET"])
@login_required
def list_resumes():
    """获取当前用户所有简历"""
    resumes = Resume.query.filter_by(user_id=g.current_user_id).order_by(Resume.updated_at.desc()).all()
    return success_response(data=[r.to_dict(include_relations=False) for r in resumes])


@resume_bp.route("/<int:resume_id>", methods=["GET"])
@login_required
def get_resume(resume_id: int):
    """获取简历详情（含所有子模块）"""
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)
    return success_response(data=r.to_dict())


@resume_bp.route("", methods=["POST"])
@login_required
def create_resume():
    """手动创建空简历"""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error_response("简历名称不能为空", 400)

    r = Resume(user_id=g.current_user_id, name=name)
    for field in ["real_name", "gender", "age", "phone", "email", "location",
                  "self_evaluation", "target_position", "target_city", "expected_salary"]:
        if field in data and data[field] is not None:
            setattr(r, field, data[field])
    db.session.add(r)
    db.session.commit()
    return success_response(data=r.to_dict(), message="简历创建成功", code=201)


@resume_bp.route("/<int:resume_id>", methods=["PUT"])
@login_required
def update_resume(resume_id: int):
    """更新简历基础信息"""
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    data = request.get_json() or {}
    for field in ["name", "real_name", "gender", "age", "phone", "email", "location",
                  "self_evaluation", "target_position", "target_city", "expected_salary",
                  "is_active"]:
        if field in data:
            val = data[field]
            if field == "age" and val:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    val = None
            setattr(r, field, val)

    db.session.commit()
    return success_response(data=r.to_dict(), message="更新成功")


@resume_bp.route("/<int:resume_id>", methods=["DELETE"])
@login_required
def delete_resume(resume_id: int):
    """删除简历"""
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    # 先删除/解除其他表对该简历的外键引用，避免完整性冲突
    from app.models.application import ApplicationRecord
    from app.models.job import JobMatchRecord

    ApplicationRecord.query.filter_by(resume_id=resume_id, user_id=g.current_user_id).update({"resume_id": None})
    JobMatchRecord.query.filter_by(resume_id=resume_id, user_id=g.current_user_id).update({"resume_id": None})
    ResumeOptimizationLog.query.filter_by(resume_id=resume_id).delete(synchronize_session=False)

    # 删除关联文件
    for path in [r.source_file_path, r.optimized_file_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.session.delete(r)
    db.session.commit()
    return success_response(message="删除成功")


# ============ 文件上传与解析 ============

@resume_bp.route("/upload", methods=["POST"])
@login_required
def upload_resume():
    """上传简历文件并自动解析"""
    if "file" not in request.files:
        return error_response("未选择文件", 400)
    file = request.files["file"]
    if not file.filename:
        return error_response("未选择文件", 400)

    try:
        file_path, file_type, original_name = _save_upload(file)
    except ValueError as e:
        return error_response(str(e), 400)

    # 解析纯文本
    try:
        raw_text = ResumeParser.parse_file(file_path, file_type)
    except Exception as e:
        logger.exception("简历文件解析失败")
        return error_response(f"文件解析失败: {e}", 500)

    # AI 结构化提取
    try:
        structured = ResumeParser.extract_structured(raw_text)
    except Exception as e:
        logger.exception("AI 结构化解析失败")
        # 即使 AI 失败，也保留文件和原文，让用户手动编辑
        structured = {
            "basic": {}, "target": {}, "self_evaluation": raw_text[:2000],
            "educations": [], "experiences": [], "projects": [], "skills": [],
        }

    # 入库
    basic = structured.get("basic", {})
    target = structured.get("target", {})
    name = request.form.get("name") or f"{basic.get('real_name') or '未命名'}的简历"

    resume = Resume(
        user_id=g.current_user_id,
        name=name,
        source_file_path=file_path,
        source_file_type=file_type,
        real_name=basic.get("real_name"),
        gender=basic.get("gender"),
        age=basic.get("age"),
        phone=basic.get("phone"),
        email=basic.get("email"),
        location=basic.get("location"),
        self_evaluation=structured.get("self_evaluation"),
        target_position=target.get("target_position"),
        target_city=target.get("target_city"),
        expected_salary=target.get("expected_salary"),
    )
    db.session.add(resume)
    db.session.flush()

    # 子模块批量入库
    for edu in structured.get("educations", []):
        db.session.add(ResumeEducation(resume_id=resume.id, **{k: v for k, v in edu.items() if v is not None}))
    for exp in structured.get("experiences", []):
        db.session.add(ResumeExperience(resume_id=resume.id, **{k: v for k, v in exp.items() if v is not None}))
    for proj in structured.get("projects", []):
        db.session.add(ResumeProject(resume_id=resume.id, **{k: v for k, v in proj.items() if v is not None}))
    for sk in structured.get("skills", []):
        db.session.add(ResumeSkill(resume_id=resume.id, **{k: v for k, v in sk.items() if v is not None}))

    db.session.commit()

    return success_response(
        data={
            "resume": resume.to_dict(),
            "raw_text": raw_text,
            "parse_warning": "AI 结构化解析失败，已保留原文供手动编辑" if not structured.get("basic") else None,
        },
        message="简历上传并解析成功",
        code=201,
    )


@resume_bp.route("/<int:resume_id>/reparse", methods=["POST"])
@login_required
def reparse_resume(resume_id: int):
    """对已有简历重新 AI 解析（用于上次解析失败后重试）"""
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    if not r.source_file_path or not os.path.exists(r.source_file_path):
        return error_response("原始文件不存在，无法重新解析", 400)

    try:
        raw_text = ResumeParser.parse_file(r.source_file_path, r.source_file_type)
        structured = ResumeParser.extract_structured(raw_text)
    except Exception as e:
        logger.exception("重新解析失败")
        return error_response(f"重新解析失败: {e}", 500)

    # 清空原有子模块数据
    ResumeEducation.query.filter_by(resume_id=r.id).delete()
    ResumeExperience.query.filter_by(resume_id=r.id).delete()
    ResumeProject.query.filter_by(resume_id=r.id).delete()
    ResumeSkill.query.filter_by(resume_id=r.id).delete()

    # 更新主表
    basic = structured.get("basic", {})
    target = structured.get("target", {})
    for k, v in basic.items():
        if v is not None:
            setattr(r, k, v)
    for k, v in target.items():
        if v is not None:
            setattr(r, k, v)
    r.self_evaluation = structured.get("self_evaluation") or r.self_evaluation

    for edu in structured.get("educations", []):
        db.session.add(ResumeEducation(resume_id=r.id, **{k: v for k, v in edu.items() if v is not None}))
    for exp in structured.get("experiences", []):
        db.session.add(ResumeExperience(resume_id=r.id, **{k: v for k, v in exp.items() if v is not None}))
    for proj in structured.get("projects", []):
        db.session.add(ResumeProject(resume_id=r.id, **{k: v for k, v in proj.items() if v is not None}))
    for sk in structured.get("skills", []):
        db.session.add(ResumeSkill(resume_id=r.id, **{k: v for k, v in sk.items() if v is not None}))

    db.session.commit()
    return success_response(data=r.to_dict(), message="重新解析成功")


# ============ 子模块增删改 ============

def _add_sub_item(model_cls, resume_id: int, user_id: int, data: dict):
    """通用：添加子模块记录"""
    try:
        r = _get_user_resume(resume_id, user_id)
    except ValueError as e:
        return None, error_response(str(e), 404)
    item = model_cls(resume_id=resume_id, **{k: v for k, v in data.items() if k != "id" and v is not None})
    db.session.add(item)
    db.session.commit()
    return item, None


@resume_bp.route("/<int:resume_id>/education", methods=["POST"])
@login_required
def add_education(resume_id: int):
    data = request.get_json() or {}
    item, err = _add_sub_item(ResumeEducation, resume_id, g.current_user_id, data)
    if err:
        return err
    return success_response(data=item.to_dict(), message="添加成功", code=201)


@resume_bp.route("/<int:resume_id>/experience", methods=["POST"])
@login_required
def add_experience(resume_id: int):
    data = request.get_json() or {}
    item, err = _add_sub_item(ResumeExperience, resume_id, g.current_user_id, data)
    if err:
        return err
    return success_response(data=item.to_dict(), message="添加成功", code=201)


@resume_bp.route("/<int:resume_id>/project", methods=["POST"])
@login_required
def add_project(resume_id: int):
    data = request.get_json() or {}
    item, err = _add_sub_item(ResumeProject, resume_id, g.current_user_id, data)
    if err:
        return err
    return success_response(data=item.to_dict(), message="添加成功", code=201)


@resume_bp.route("/<int:resume_id>/skill", methods=["POST"])
@login_required
def add_skill(resume_id: int):
    data = request.get_json() or {}
    item, err = _add_sub_item(ResumeSkill, resume_id, g.current_user_id, data)
    if err:
        return err
    return success_response(data=item.to_dict(), message="添加成功", code=201)


@resume_bp.route("/<int:resume_id>/education/<int:item_id>", methods=["PUT", "DELETE"])
@login_required
def manage_education(resume_id: int, item_id: int):
    return _manage_sub_item(ResumeEducation, resume_id, item_id, g.current_user_id)


@resume_bp.route("/<int:resume_id>/experience/<int:item_id>", methods=["PUT", "DELETE"])
@login_required
def manage_experience(resume_id: int, item_id: int):
    return _manage_sub_item(ResumeExperience, resume_id, item_id, g.current_user_id)


@resume_bp.route("/<int:resume_id>/project/<int:item_id>", methods=["PUT", "DELETE"])
@login_required
def manage_project(resume_id: int, item_id: int):
    return _manage_sub_item(ResumeProject, resume_id, item_id, g.current_user_id)


@resume_bp.route("/<int:resume_id>/skill/<int:item_id>", methods=["PUT", "DELETE"])
@login_required
def manage_skill(resume_id: int, item_id: int):
    return _manage_sub_item(ResumeSkill, resume_id, item_id, g.current_user_id)


def _manage_sub_item(model_cls, resume_id: int, item_id: int, user_id: int):
    """通用：更新/删除子模块"""
    try:
        _get_user_resume(resume_id, user_id)
    except ValueError as e:
        return error_response(str(e), 404)
    item = model_cls.query.filter_by(id=item_id, resume_id=resume_id).first()
    if not item:
        return error_response("记录不存在", 404)

    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return success_response(message="删除成功")
    else:
        data = request.get_json() or {}
        for k, v in data.items():
            if k != "id" and k != "resume_id" and hasattr(item, k):
                setattr(item, k, v)
        db.session.commit()
        return success_response(data=item.to_dict(), message="更新成功")


# ============ AI 优化 ============

@resume_bp.route("/<int:resume_id>/optimize", methods=["POST"])
@login_required
def optimize_resume(resume_id: int):
    """
    生成 AI 优化建议（不直接修改简历）
    请求体：{"jd": "目标岗位JD", "template_id": 123}
    """
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    data = request.get_json() or {}
    jd = (data.get("jd") or "").strip()
    template_id = data.get("template_id")
    if not jd:
        return error_response("请提供目标岗位 JD", 400)

    template = None
    if template_id:
        template = JobTemplate.query.filter_by(id=template_id, user_id=g.current_user_id).first()

    try:
        suggestions = ResumeOptimizer.generate_suggestions(r, jd, template)
    except Exception as e:
        logger.exception("AI 优化建议生成失败")
        return error_response(f"AI 优化失败: {e}", 500)

    log = ResumeOptimizationLog(
        resume_id=r.id,
        target_jd=jd,
        target_template_id=template_id,
        keyword_suggestions=suggestions["keyword_suggestions"],
        deletion_suggestions=suggestions["deletion_suggestions"],
        skill_suggestions=suggestions["skill_suggestions"],
        evaluation_suggestions=suggestions["evaluation_suggestions"],
        format_suggestions=suggestions["format_suggestions"],
        status="pending",
    )
    db.session.add(log)
    db.session.commit()

    return success_response(
        data={
            "log_id": log.id,
            "suggestions": log.to_dict(),
        },
        message="优化建议生成成功，请确认后应用",
    )


@resume_bp.route("/<int:resume_id>/optimize/<int:log_id>/apply", methods=["POST"])
@login_required
def apply_optimization(resume_id: int, log_id: int):
    """
    用户确认后应用优化建议
    请求体：{"fields": {"self_evaluation": "...", "skills": [...], ...}}
    """
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    log = ResumeOptimizationLog.query.filter_by(id=log_id, resume_id=resume_id).first()
    if not log:
        return error_response("优化记录不存在", 404)

    data = request.get_json() or {}
    fields = data.get("fields", {})

    try:
        ResumeOptimizer.apply_suggestions(r, log, fields)
    except Exception as e:
        logger.exception("应用优化建议失败")
        return error_response(f"应用失败: {e}", 500)

    import datetime
    log.status = "applied"
    log.applied_at = datetime.datetime.utcnow()
    db.session.commit()

    return success_response(data=r.to_dict(), message="优化建议已应用")


# ============ PDF 导出 ============

@resume_bp.route("/<int:resume_id>/export-pdf", methods=["POST"])
@login_required
def export_pdf(resume_id: int):
    """导出简历为 PDF"""
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    data = request.get_json() or {}
    pages = data.get("pages", "single")  # single / multi

    try:
        pdf_path = ResumePDFGenerator.generate(r, pages=pages)
    except Exception as e:
        logger.exception("PDF 生成失败")
        return error_response(f"PDF 生成失败: {e}", 500)

    r.optimized_file_path = pdf_path
    db.session.commit()

    return success_response(
        data={
            "pdf_path": pdf_path,
            "download_url": f"/api/resume/{resume_id}/download-pdf",
        },
        message="PDF 生成成功",
    )


@resume_bp.route("/<int:resume_id>/download-pdf", methods=["GET"])
@login_required
def download_pdf(resume_id: int):
    """下载 PDF 文件"""
    try:
        r = _get_user_resume(resume_id, g.current_user_id)
    except ValueError as e:
        return error_response(str(e), 404)

    pdf_path = r.optimized_file_path
    if not pdf_path or not os.path.exists(pdf_path):
        return error_response("PDF 文件不存在，请先生成", 404)

    return send_file(pdf_path, as_attachment=True,
                     download_name=f"{r.name or 'resume'}.pdf")
