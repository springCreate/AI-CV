"""
用户模型
"""
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True, comment="登录用户名")
    password_hash = db.Column(db.String(256), nullable=False, comment="密码哈希")
    nickname = db.Column(db.String(64), comment="昵称")
    email = db.Column(db.String(128), comment="邮箱")
    phone = db.Column(db.String(32), comment="手机号")

    # 求职意向摘要（用于简历自我评价生成）
    target_position = db.Column(db.String(128), comment="目标岗位，如：软件测试")
    target_city = db.Column(db.String(64), comment="期望城市")
    expected_salary_min = db.Column(db.Integer, comment="期望最低薪资（元/月）")

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "phone": self.phone,
            "target_position": self.target_position,
            "target_city": self.target_city,
            "expected_salary_min": self.expected_salary_min,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data
