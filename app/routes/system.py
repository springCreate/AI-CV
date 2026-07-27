"""
系统级路由：配置检查、健康检查、AI 连通性测试
"""
from flask import Blueprint, current_app
from app.services.ai_service import DeepSeekService
from app.utils.decorators import login_required
from app.utils.responses import success_response, error_response

system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return success_response(data={"status": "ok"})


@system_bp.route("/config", methods=["GET"])
@login_required
def get_config_status():
    """获取系统配置状态（脱敏）"""
    cfg = current_app.config["DEEPSEEK_CFG"]

    return success_response(data={
        "deepseek": {
            "configured": bool(cfg.get("api_key")) and not cfg.get("api_key", "").startswith("sk-xxxxxxx"),
            "model": cfg.get("model"),
            "base_url": cfg.get("base_url"),
            "max_context_tokens": cfg.get("max_context_tokens"),
        },
    })


@system_bp.route("/ai/test", methods=["POST"])
@login_required
def test_ai():
    """测试 DeepSeek API 连通性"""
    result = DeepSeekService.test_connection()
    if result["success"]:
        return success_response(data=result, message=result["message"])
    return error_response(result["message"], 500, data=result)
