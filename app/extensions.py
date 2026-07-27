"""
Flask 扩展初始化（避免循环导入）
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
