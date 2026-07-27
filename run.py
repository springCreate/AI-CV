"""
AI 智能简历适配与多平台岗位匹配投递系统
启动入口
"""
import os
import sys
from pathlib import Path

# 确保项目根目录在 PYTHONPATH 中
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db


def init_dirs():
    """初始化本地存储目录"""
    dirs = ["data", "data/resumes", "data/optimized", "data/exports", "data/logs"]
    for d in dirs:
        p = BASE_DIR / d
        p.mkdir(parents=True, exist_ok=True)


def ensure_config():
    """首次运行时自动从 example 复制配置文件"""
    cfg = BASE_DIR / "config.yaml"
    example = BASE_DIR / "config.example.yaml"
    if not cfg.exists() and example.exists():
        import shutil
        shutil.copy(example, cfg)
        print("[初始化] 已从 config.example.yaml 创建 config.yaml，请编辑后填入 DeepSeek API Key")


def main():
    init_dirs()
    ensure_config()
    app = create_app()

    # 首次运行自动建表
    with app.app_context():
        db.create_all()
        app.logger.info("数据库初始化完成")

    # 读取运行配置
    host = app.config.get("SERVER_HOST", "127.0.0.1")
    port = app.config.get("SERVER_PORT", 5000)
    debug = app.config.get("DEBUG", False)

    print("=" * 60)
    print("  AI 智能简历适配与多平台岗位匹配投递系统")
    print("=" * 60)
    print(f"  访问地址: http://{host}:{port}")
    print(f"  调试模式: {'开启' if debug else '关闭'}")
    print(f"  数据目录: {BASE_DIR / 'data'}")
    print("=" * 60)
    print("  按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
