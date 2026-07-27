"""
简历相关模型
"""
import datetime
from app.extensions import db


class Resume(db.Model):
    """简历主表"""
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True, comment="所属用户")

    name = db.Column(db.String(64), nullable=False, comment="简历名称，如：张三-测试工程师")
    source_file_path = db.Column(db.String(512), comment="原始上传文件路径")
    source_file_type = db.Column(db.String(16), comment="原始文件类型：pdf/docx")

    # 个人基础信息
    real_name = db.Column(db.String(64), comment="姓名")
    gender = db.Column(db.String(16), comment="性别")
    age = db.Column(db.Integer, comment="年龄")
    phone = db.Column(db.String(32), comment="电话")
    email = db.Column(db.String(128), comment="邮箱")
    location = db.Column(db.String(128), comment="现居地")

    # 自我评价
    self_evaluation = db.Column(db.Text, comment="自我评价")

    # 求职意向
    target_position = db.Column(db.String(128), comment="目标岗位")
    target_city = db.Column(db.String(64), comment="期望城市")
    expected_salary = db.Column(db.String(64), comment="期望薪资")

    # 状态
    is_active = db.Column(db.Boolean, default=True, comment="是否当前激活简历")
    optimized_file_path = db.Column(db.String(512), comment="AI 优化后 PDF 路径")

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联
    educations = db.relationship("ResumeEducation", backref="resume", cascade="all, delete-orphan",
                                 lazy="dynamic", order_by="ResumeEducation.start_date.desc()")
    experiences = db.relationship("ResumeExperience", backref="resume", cascade="all, delete-orphan",
                                  lazy="dynamic", order_by="ResumeExperience.start_date.desc()")
    projects = db.relationship("ResumeProject", backref="resume", cascade="all, delete-orphan",
                               lazy="dynamic", order_by="ResumeProject.start_date.desc()")
    skills = db.relationship("ResumeSkill", backref="resume", cascade="all, delete-orphan",
                             lazy="dynamic")
    optimization_logs = db.relationship("ResumeOptimizationLog", backref="resume",
                                        lazy="dynamic", order_by="ResumeOptimizationLog.created_at.desc()")

    def to_dict(self, include_relations=True):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "source_file_path": self.source_file_path,
            "source_file_type": self.source_file_type,
            "real_name": self.real_name,
            "gender": self.gender,
            "age": self.age,
            "phone": self.phone,
            "email": self.email,
            "location": self.location,
            "self_evaluation": self.self_evaluation,
            "target_position": self.target_position,
            "target_city": self.target_city,
            "expected_salary": self.expected_salary,
            "is_active": self.is_active,
            "optimized_file_path": self.optimized_file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["educations"] = [e.to_dict() for e in self.educations]
            data["experiences"] = [e.to_dict() for e in self.experiences]
            data["projects"] = [p.to_dict() for p in self.projects]
            data["skills"] = [s.to_dict() for s in self.skills]
        return data


class ResumeEducation(db.Model):
    """教育经历"""
    __tablename__ = "resume_educations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    school = db.Column(db.String(128), nullable=False, comment="学校")
    major = db.Column(db.String(128), comment="专业")
    degree = db.Column(db.String(32), comment="学历：大专/本科/硕士/博士")
    start_date = db.Column(db.String(16), comment="开始时间，如 2021-09")
    end_date = db.Column(db.String(16), comment="结束时间，如 2025-06 或 至今")
    description = db.Column(db.Text, comment="补充描述")

    def to_dict(self):
        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "school": self.school,
            "major": self.major,
            "degree": self.degree,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
        }


class ResumeExperience(db.Model):
    """工作 / 实习经历"""
    __tablename__ = "resume_experiences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    company = db.Column(db.String(128), nullable=False, comment="公司名称")
    position = db.Column(db.String(128), comment="职位")
    job_type = db.Column(db.String(32), comment="类型：全职/实习")
    start_date = db.Column(db.String(16), comment="开始时间")
    end_date = db.Column(db.String(16), comment="结束时间")
    description = db.Column(db.Text, comment="工作内容描述（STAR 法则）")

    def to_dict(self):
        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "company": self.company,
            "position": self.position,
            "job_type": self.job_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
        }


class ResumeProject(db.Model):
    """项目经历"""
    __tablename__ = "resume_projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, comment="项目名称")
    role = db.Column(db.String(64), comment="担任角色")
    start_date = db.Column(db.String(16), comment="开始时间")
    end_date = db.Column(db.String(16), comment="结束时间")
    description = db.Column(db.Text, comment="项目描述（STAR 法则）")
    tech_stack = db.Column(db.String(256), comment="技术栈，逗号分隔")

    def to_dict(self):
        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "name": self.name,
            "role": self.role,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "tech_stack": self.tech_stack,
        }


class ResumeSkill(db.Model):
    """专业技能"""
    __tablename__ = "resume_skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, comment="技能名称，如：Python")
    level = db.Column(db.String(32), comment="掌握程度：了解/熟悉/熟练/精通")
    category = db.Column(db.String(32), comment="分类：编程语言/工具/框架/软技能")

    def to_dict(self):
        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "name": self.name,
            "level": self.level,
            "category": self.category,
        }


class ResumeOptimizationLog(db.Model):
    """简历 AI 优化记录（用于审计与回溯）"""
    __tablename__ = "resume_optimization_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    target_jd = db.Column(db.Text, comment="目标岗位 JD")
    target_template_id = db.Column(db.Integer, comment="使用的求职诉求模板 ID")

    # 五大维度优化建议（JSON 字符串）
    keyword_suggestions = db.Column(db.Text, comment="关键词适配改写建议")
    deletion_suggestions = db.Column(db.Text, comment="无关内容删减建议")
    skill_suggestions = db.Column(db.Text, comment="技能补充建议")
    evaluation_suggestions = db.Column(db.Text, comment="自我评价生成建议")
    format_suggestions = db.Column(db.Text, comment="排版优化建议")

    # 用户确认状态
    status = db.Column(db.String(16), default="pending", comment="pending/applied/rejected")
    applied_at = db.Column(db.DateTime, comment="用户确认应用时间")

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        import json
        def safe_loads(s):
            try:
                return json.loads(s) if s else None
            except Exception:
                return s
        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "target_jd": self.target_jd,
            "target_template_id": self.target_template_id,
            "keyword_suggestions": safe_loads(self.keyword_suggestions),
            "deletion_suggestions": safe_loads(self.deletion_suggestions),
            "skill_suggestions": safe_loads(self.skill_suggestions),
            "evaluation_suggestions": safe_loads(self.evaluation_suggestions),
            "format_suggestions": safe_loads(self.format_suggestions),
            "status": self.status,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
