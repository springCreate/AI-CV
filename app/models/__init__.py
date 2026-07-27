"""
数据模型汇总导入
"""
from app.models.user import User
from app.models.resume import (
    Resume, ResumeEducation, ResumeExperience,
    ResumeProject, ResumeSkill, ResumeOptimizationLog
)
from app.models.template import JobTemplate
from app.models.job import Job, JobMatchRecord, Blacklist, JobRefreshLog
from app.models.application import ApplicationRecord

__all__ = [
    "User",
    "Resume", "ResumeEducation", "ResumeExperience",
    "ResumeProject", "ResumeSkill", "ResumeOptimizationLog",
    "JobTemplate",
    "Job", "JobMatchRecord", "Blacklist", "JobRefreshLog",
    "ApplicationRecord",
]
