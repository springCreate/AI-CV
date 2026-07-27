"""
DeepSeek AI 服务层

核心能力：
1. 封装 DeepSeek API 调用（OpenAI 兼容协议）
2. Token 容错机制：超长文本自动分片 + 截断
3. 统一重试、超时、错误处理
4. JSON 结构化输出
"""
import json
import time
import logging
from typing import Optional, Dict, Any, List

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from app.utils.token_manager import (
    count_tokens, build_safe_payload, split_text_by_tokens,
    USABLE_MAX_TOKENS
)

logger = logging.getLogger(__name__)


class DeepSeekService:
    """DeepSeek AI 服务"""

    _client = None
    _config = None

    @classmethod
    def _get_client(cls):
        """懒加载 OpenAI 客户端（DeepSeek 兼容协议）"""
        if cls._client is None:
            from flask import current_app
            cfg = current_app.config["DEEPSEEK_CFG"]
            cls._config = cfg
            cls._client = OpenAI(
                api_key=cfg["api_key"],
                base_url=cfg["base_url"],
                timeout=cfg.get("timeout", 120),
                max_retries=cfg.get("max_retries", 3),
            )
        return cls._client

    @classmethod
    def _reset_client(cls):
        """重置客户端（配置变更时使用）"""
        cls._client = None
        cls._config = None

    @classmethod
    def _ensure_config(cls):
        """确保配置已加载"""
        if cls._config is None:
            cls._get_client()
        return cls._config

    @classmethod
    def is_configured(cls) -> bool:
        """检查 API Key 是否已配置"""
        try:
            cfg = cls._ensure_config()
            key = cfg.get("api_key", "")
            return bool(key) and not key.startswith("sk-xxxxxxx")
        except Exception:
            return False

    @classmethod
    def chat(cls,
             system_prompt: str,
             user_content: str,
             json_mode: bool = False,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        标准对话调用（含 Token 容错）

        Returns:
            {
                "content": str,        # 模型响应文本
                "truncated": bool,     # 输入是否被截断
                "warning": str,        # 警告信息（如有）
                "usage": dict,         # token 使用统计
            }
        """
        client = cls._get_client()
        cfg = cls._ensure_config()
        model = cfg.get("model", "deepseek-chat")
        max_context = cfg.get("max_context_tokens", USABLE_MAX_TOKENS)

        # Token 容错：构建安全 payload
        payload = build_safe_payload(system_prompt, user_content, max_context, model)
        content = payload["content"]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else cfg.get("temperature", 0.5),
            "max_tokens": max_tokens or cfg.get("max_output_tokens", 4096),
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(1, cfg.get("max_retries", 3) + 1):
            try:
                logger.info("DeepSeek 调用 attempt=%d, model=%s, input_tokens≈%d",
                            attempt, model, payload["used_tokens"])
                response = client.chat.completions.create(**kwargs)
                result = {
                    "content": response.choices[0].message.content or "",
                    "truncated": payload["truncated"],
                    "warning": payload.get("warning"),
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                }
                logger.info("DeepSeek 调用成功, total_tokens=%d", result["usage"]["total_tokens"])
                return result

            except APITimeoutError as e:
                last_error = f"请求超时: {e}"
                logger.warning("DeepSeek 超时 attempt=%d: %s", attempt, e)
            except RateLimitError as e:
                last_error = f"触发限流: {e}"
                logger.warning("DeepSeek 限流 attempt=%d: %s", attempt, e)
                time.sleep(2 ** attempt)
            except APIError as e:
                last_error = f"API 错误: {e}"
                logger.error("DeepSeek API 错误 attempt=%d: %s", attempt, e)
                # 400 错误一般是 token 超限或参数问题，重试无意义
                if "400" in str(e) or "context_length" in str(e).lower():
                    # 二次截断：把内容砍半重试一次
                    half = max(1000, payload["used_tokens"] // 2)
                    from app.utils.token_manager import truncate_to_tokens
                    content = truncate_to_tokens(content, half, model)
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content + "\n\n[注：原文过长，已截断]"},
                    ]
                    kwargs["messages"] = messages
                    logger.warning("触发 400 错误，二次截断至 %d tokens 重试", half)
            except Exception as e:
                last_error = f"未知错误: {e}"
                logger.exception("DeepSeek 调用异常 attempt=%d", attempt)

            if attempt < cfg.get("max_retries", 3):
                time.sleep(1.5 * attempt)

        raise RuntimeError(f"DeepSeek 调用失败（已重试 {cfg.get('max_retries', 3)} 次）: {last_error}")

    @classmethod
    def chat_json(cls, system_prompt: str, user_content: str,
                  temperature: Optional[float] = None) -> Dict:
        """
        调用并解析 JSON 响应（容错：尝试多种方式提取 JSON）
        """
        result = cls.chat(system_prompt, user_content,
                          json_mode=True, temperature=temperature)
        content = result["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试从 markdown 代码块中提取
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # 尝试提取首个 JSON 对象
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            logger.error("JSON 解析失败，原始内容: %s", content[:500])
            raise ValueError(f"AI 返回内容无法解析为 JSON: {content[:200]}")

    @classmethod
    def chat_long_text(cls, system_prompt: str, long_content: str,
                       chunk_handler=None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        处理超长文本：自动分片调用 + 结果合并

        Args:
            system_prompt: 系统提示词
            long_content: 超长用户内容
            chunk_handler: 可选的分片结果合并函数 (list[str]) -> str
            temperature: 温度

        Returns:
            {"content": str, "chunks": int, "truncated": bool}
        """
        cfg = cls._ensure_config()
        max_context = cfg.get("max_context_tokens", USABLE_MAX_TOKENS)
        sys_tokens = count_tokens(system_prompt)
        # 单片预留 8k 给响应
        chunk_size = min(60000, max_context - sys_tokens - 8192)
        if chunk_size <= 0:
            raise ValueError("system prompt 过长，无法分片处理")

        chunks = split_text_by_tokens(long_content, chunk_size=chunk_size, overlap=500)
        if len(chunks) == 1:
            result = cls.chat(system_prompt, chunks[0], temperature=temperature)
            return {
                "content": result["content"],
                "chunks": 1,
                "truncated": result["truncated"],
            }

        logger.info("长文本分片处理，共 %d 片，单片 ≤%d tokens", len(chunks), chunk_size)
        partial_results = []
        for i, chunk in enumerate(chunks, 1):
            logger.info("处理分片 %d/%d", i, len(chunks))
            prompt = f"{system_prompt}\n\n[当前为长文本第 {i}/{len(chunks)} 片，请仅针对本片内容处理]"
            result = cls.chat(prompt, chunk, temperature=temperature)
            partial_results.append(result["content"])

        if chunk_handler and callable(chunk_handler):
            merged = chunk_handler(partial_results)
        else:
            merged = "\n\n---\n\n".join(partial_results)

        return {
            "content": merged,
            "chunks": len(chunks),
            "truncated": False,
        }

    @classmethod
    def test_connection(cls) -> Dict[str, Any]:
        """测试 API 连通性"""
        try:
            result = cls.chat(
                "你是一个测试助手",
                "请回复：连接成功",
                max_tokens=20,
            )
            return {
                "success": True,
                "message": "DeepSeek API 连接正常",
                "response": result["content"][:100],
                "usage": result["usage"],
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {e}",
            }
