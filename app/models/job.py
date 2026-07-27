"""
岗位与匹配相关模型
"""
import datetime
from app.extensions import db


class Job(db.Model):
    """岗位信息（从招聘平台拉取并缓存）"""
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True, comment="所属用户（隔离）")

    # 平台与原始 ID
    platform = db.Column(db.String(32), nullable=False, index=True, comment="来源：boss/zhilian/51job/shixiseng/mock")
    platform_job_id = db.Column(db.String(128), comment="平台原始岗位 ID")

    # 岗位核心字段
    title = db.Column(db.String(256), nullable=False, comment="岗位名称")
    company = db.Column(db.String(256), nullable=False, comment="公司名称")
    city = db.Column(db.String(64), comment="工作城市")
    district = db.Column(db.String(64), comment="区域")
    salary_min = db.Column(db.Integer, comment="月薪下限（元）")
    salary_max = db.Column(db.Integer, comment="月薪上限（元）")
    salary_text = db.Column(db.String(64), comment="薪资原文，如 8-12K·13薪")

    # 要求
    work_years = db.Column(db.String(32), comment="工作年限要求，如 3-5年")
    education = db.Column(db.String(32), comment="学历要求")
    job_type = db.Column(db.String(32), comment="全职/实习")

    # 作息福利
    is_weekend_off = db.Column(db.Boolean, comment="是否双休")
    has_accommodation = db.Column(db.Boolean, comment="是否包住宿")

    # 详细信息
    jd_text = db.Column(db.Text, comment="岗位描述全文")
    company_size = db.Column(db.String(64), comment="公司规模")
    company_industry = db.Column(db.String(64), comment="公司行业")
    hr_name = db.Column(db.String(64), comment="HR 名称（如有）")
    publish_time = db.Column(db.DateTime, comment="发布时间")
    job_url = db.Column(db.String(512), comment="岗位原链接")

    # 元数据
    first_fetched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, comment="首次抓取时间")
    last_fetched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                                comment="最近抓取时间")

    __table_args__ = (
        db.UniqueConstraint("user_id", "platform", "platform_job_id", name="uq_user_platform_job"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "platform_job_id": self.platform_job_id,
            "title": self.title,
            "company": self.company,
            "city": self.city,
            "district": self.district,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_text": self.salary_text,
            "work_years": self.work_years,
            "education": self.education,
            "job_type": self.job_type,
            "is_weekend_off": self.is_weekend_off,
            "has_accommodation": self.has_accommodation,
            "jd_text": self.jd_text,
            "company_size": self.company_size,
            "company_industry": self.company_industry,
            "hr_name": self.hr_name,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "job_url": self.job_url,
            "first_fetched_at": self.first_fetched_at.isoformat() if self.first_fetched_at else None,
            "last_fetched_at": self.last_fetched_at.isoformat() if self.last_fetched_at else None,
        }


class JobMatchRecord(db.Model):
    """岗位匹配记录（含 AI 打分）"""
    __tablename__ = "job_match_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), comment="匹配所用简历")
    template_id = db.Column(db.Integer, db.ForeignKey("job_templates.id"), comment="匹配所用模板")

    # 硬性过滤
    hard_filter_passed = db.Column(db.Boolean, default=False, comment="是否通过硬性条件过滤")
    hard_filter_reason = db.Column(db.String(256), comment="未通过原因")

    # AI 软性打分
    match_score = db.Column(db.Integer, default=0, comment="匹配度评分 0-100")
    score_details = db.Column(db.Text, comment="评分明细 JSON")
    match_summary = db.Column(db.Text, comment="匹配分析摘要")
    missing_skills = db.Column(db.Text, comment="缺失技能，逗号分隔")

    is_new = db.Column(db.Boolean, default=True, comment="是否新匹配（用于提醒）")
    notified = db.Column(db.Boolean, default=False, comment="是否已推送提醒")

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # 关联
    job = db.relationship("Job", backref="match_records", lazy="joined")

    def to_dict(self, include_job=True):
        import json
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "resume_id": self.resume_id,
            "template_id": self.template_id,
            "hard_filter_passed": self.hard_filter_passed,
            "hard_filter_reason": self.hard_filter_reason,
            "match_score": self.match_score,
            "score_details": json.loads(self.score_details) if self.score_details else None,
            "match_summary": self.match_summary,
            "missing_skills": self.missing_skills.split(",") if self.missing_skills else [],
            "is_new": self.is_new,
            "notified": self.notified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_job and self.job:
            data["job"] = self.job.to_dict()
        return data


class Blacklist(db.Model):
    """公司黑名单"""
    __tablename__ = "blacklists"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    company = db.Column(db.String(256), nullable=False, comment="公司名称")
    reason = db.Column(db.String(256), comment="拉黑原因")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "company", name="uq_user_blacklist_company"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company": self.company,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class JobRefreshLog(db.Model):
    """岗位刷新日志"""
    __tablename__ = "job_refresh_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    platform = db.Column(db.String(32), comment="平台，空表示全平台")
    new_job_count = db.Column(db.Integer, default=0, comment="新增岗位数")
    high_match_count = db.Column(db.Integer, default=0, comment="高匹配度岗位数")
    status = db.Column(db.String(16), default="success", comment="success/failed")
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    finished_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "new_job_count": self.new_job_count,
            "high_match_count": self.high_match_count,
            "status": self.status,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
