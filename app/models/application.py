"""
投递记录模型
"""
import datetime
from app.extensions import db


class ApplicationRecord(db.Model):
    """岗位投递记录"""
    __tablename__ = "application_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), comment="投递所用简历")

    # 投递状态
    status = db.Column(db.String(16), default="not_applied",
                       comment="not_applied/applied/interview/offer/rejected")
    applied_at = db.Column(db.DateTime, comment="投递时间")
    applied_via = db.Column(db.String(32), comment="投递渠道：手动跳转/外部")

    # AI 生成的投递辅助资料
    greeting_message = db.Column(db.Text, comment="AI 生成的打招呼话术")
    self_introduction = db.Column(db.Text, comment="AI 生成的定制化自我介绍")

    # 备注
    remark = db.Column(db.Text, comment="用户备注")

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    job = db.relationship("Job", backref="applications", lazy="joined")

    def to_dict(self, include_job=True):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "resume_id": self.resume_id,
            "status": self.status,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "applied_via": self.applied_via,
            "greeting_message": self.greeting_message,
            "self_introduction": self.self_introduction,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_job and self.job:
            data["job"] = self.job.to_dict()
        return data
