"""
求职诉求模板模型
"""
import datetime
from app.extensions import db


class JobTemplate(db.Model):
    """求职诉求模板"""
    __tablename__ = "job_templates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True, comment="所属用户")

    name = db.Column(db.String(64), nullable=False, comment="模板名称，如：北京测试岗-8k双休")
    is_default = db.Column(db.Boolean, default=False, comment="是否默认模板")

    # 硬性筛选条件
    cities = db.Column(db.String(256), comment="期望城市，逗号分隔，如：北京,天津")
    position = db.Column(db.String(128), comment="目标岗位，如：软件测试")
    job_type = db.Column(db.String(32), comment="全职/实习")
    salary_min = db.Column(db.Integer, comment="最低月薪（元），如 8000")
    salary_max = db.Column(db.Integer, comment="最高月薪（元）")
    work_years_min = db.Column(db.Integer, comment="最少工作年限要求")
    work_years_max = db.Column(db.Integer, comment="最多工作年限要求")

    # 作息与福利
    require_weekend_off = db.Column(db.Boolean, default=False, comment="是否必须双休")
    require_no_overtime = db.Column(db.Boolean, default=False, comment="是否要求不加班")
    require_accommodation = db.Column(db.Boolean, default=False, comment="是否要求包住宿")

    # 实习专属
    intern_certificate = db.Column(db.Boolean, default=False, comment="是否要求可开实习证明")
    intern_min_months = db.Column(db.Integer, comment="实习最短月数")

    # 其他要求（自由文本）
    other_requirements = db.Column(db.Text, comment="其他自定义要求")
    keywords = db.Column(db.Text, comment="关键词，逗号分隔，用于 AI 软性匹配加权")

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "is_default": self.is_default,
            "cities": self.cities.split(",") if self.cities else [],
            "position": self.position,
            "job_type": self.job_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "work_years_min": self.work_years_min,
            "work_years_max": self.work_years_max,
            "require_weekend_off": self.require_weekend_off,
            "require_no_overtime": self.require_no_overtime,
            "require_accommodation": self.require_accommodation,
            "intern_certificate": self.intern_certificate,
            "intern_min_months": self.intern_min_months,
            "other_requirements": self.other_requirements,
            "keywords": self.keywords.split(",") if self.keywords else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
