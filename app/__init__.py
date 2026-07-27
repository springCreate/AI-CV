"""
应用工厂模块
"""
import os
import yaml
import logging
from pathlib import Path
from flask import Flask, send_from_directory
from flask_cors import CORS
from logging.handlers import RotatingFileHandler

from app.extensions import db
from app.utils.responses import error_response

BASE_DIR = Path(__file__).resolve().parent.parent


def load_config():
    """加载 YAML 配置文件"""
    cfg_path = BASE_DIR / "config.yaml"
    if not cfg_path.exists():
        cfg_path = BASE_DIR / "config.example.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(app, cfg):
    """配置日志"""
    log_cfg = cfg.get("logging", {})
    log_dir = BASE_DIR / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / log_cfg.get("file", "data/logs/app.log").split("/")[-1]

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    app.logger.setLevel(level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)


def register_blueprints(app):
    """注册所有 API 蓝图"""
    from app.routes.auth import auth_bp
    from app.routes.resume import resume_bp
    from app.routes.template import template_bp
    from app.routes.job import job_bp
    from app.routes.application import application_bp
    from app.routes.system import system_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(resume_bp, url_prefix="/api/resume")
    app.register_blueprint(template_bp, url_prefix="/api/template")
    app.register_blueprint(job_bp, url_prefix="/api/job")
    app.register_blueprint(application_bp, url_prefix="/api/application")
    app.register_blueprint(system_bp, url_prefix="/api/system")


def create_app():
    """创建 Flask 应用实例"""
    app = Flask(__name__, static_folder=str(BASE_DIR / "static"), static_url_path="")
    cfg = load_config()

    # 基础配置
    app.config["SECRET_KEY"] = cfg["server"]["secret_key"]
    # SQLite 路径处理：相对路径转为基于项目根目录的绝对路径
    db_uri = cfg["database"]["uri"]
    if db_uri.startswith("sqlite:///") and not db_uri.startswith("sqlite:////"):
        rel_path = db_uri[len("sqlite:///"):]
        abs_path = str((BASE_DIR / rel_path).resolve())
        db_uri = f"sqlite:///{abs_path}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = cfg["database"].get("track_modifications", False)
    app.config["MAX_CONTENT_LENGTH"] = cfg["storage"].get("max_upload_mb", 20) * 1024 * 1024

    # 自定义配置
    app.config["SERVER_HOST"] = cfg["server"].get("host", "127.0.0.1")
    app.config["SERVER_PORT"] = cfg["server"].get("port", 5000)
    app.config["DEBUG"] = cfg["server"].get("debug", False)
    app.config["DEEPSEEK_CFG"] = cfg["deepseek"]
    app.config["JOB_PLATFORMS_CFG"] = cfg["job_platforms"]
    app.config["JOB_REFRESH_CFG"] = cfg.get("job_refresh", {})
    app.config["STORAGE_CFG"] = cfg["storage"]
    app.config["BASE_DIR"] = str(BASE_DIR)

    # 初始化扩展
    db.init_app(app)
    CORS(app, supports_credentials=True)

    # 日志
    setup_logging(app, cfg)

    # 注册蓝图
    register_blueprints(app)

    # 全局错误处理
    register_error_handlers(app)

    # 静态文件入口（前端 SPA）
    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def static_proxy(path):
        full_path = os.path.join(app.static_folder, path)
        if os.path.exists(full_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    app.logger.info("应用创建完成")
    return app


def register_error_handlers(app):
    """全局错误处理"""

    @app.errorhandler(400)
    def bad_request(e):
        return error_response(str(e) or "请求参数错误", 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response("未登录或登录已过期", 401)

    @app.errorhandler(403)
    def forbidden(e):
        return error_response("无权限访问", 403)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("资源不存在", 404)

    @app.errorhandler(413)
    def too_large(e):
        return error_response("上传文件过大", 413)

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("服务器内部错误: %s", e)
        return error_response("服务器内部错误", 500)
