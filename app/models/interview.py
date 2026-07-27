"""
面试问题模型
"""
from datetime import datetime
from app.extensions import db


class InterviewQuestion(db.Model):
    """面试问题记录"""
    __tablename__ = "interview_questions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False)

    question = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(32), nullable=False)
    difficulty = db.Column(db.String(16), default="medium")
    key_points = db.Column(db.Text, default="")
    answer_approach = db.Column(db.Text, default="")
    sample_answer = db.Column(db.Text, default="")
    bonus_points = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", backref=db.backref("interview_questions", lazy="dynamic"))
    resume = db.relationship("Resume", backref=db.backref("interview_questions", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "type": self.type,
            "difficulty": self.difficulty,
            "key_points": [p.strip() for p in self.key_points.split(",") if p.strip()] if self.key_points else [],
            "answer_approach": self.answer_approach,
            "sample_answer": self.sample_answer,
            "bonus_points": [p.strip() for p in self.bonus_points.split(",") if p.strip()] if self.bonus_points else [],
            "job_id": self.job_id,
            "job": self.job.to_dict() if self.job else None,
            "resume_id": self.resume_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
