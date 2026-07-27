"""
Token 管理工具
解决 DeepSeek 模型 1048576 Token 上限问题，提供长文本分片与截断能力
"""
try:
    import tiktoken
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False
    tiktoken = None

from functools import lru_cache
from typing import List


# DeepSeek 模型 Token 上限（保留 8k 安全边距用于响应）
DEEPSEEK_MAX_TOKENS = 1048576
SAFE_RESERVE_TOKENS = 8192
USABLE_MAX_TOKENS = DEEPSEEK_MAX_TOKENS - SAFE_RESERVE_TOKENS


@lru_cache(maxsize=4)
def get_encoder(model: str = "deepseek-chat"):
    """
    获取 Token 计数器。
    DeepSeek 使用与 GPT-2/4 类似的 BPE 分词，cl100k_base 近似度较高。
    """
    if _HAS_TIKTOKEN:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            pass
    return None


def count_tokens(text: str, model: str = "deepseek-chat") -> int:
    """统计文本 Token 数"""
    if not text:
        return 0
    encoder = get_encoder(model)
    if encoder is not None:
        try:
            return len(encoder.encode(text))
        except Exception:
            pass
    # 兜底估算：中英文混合约 1 token ≈ 2.5 字符
    return max(1, len(text) // 2)


def truncate_to_tokens(text: str, max_tokens: int, model: str = "deepseek-chat") -> str:
    """按 Token 数截断文本，保留前 max_tokens 个 token"""
    if not text:
        return ""
    encoder = get_encoder(model)
    if encoder is None:
        # 兜底：按字符估算
        char_limit = max_tokens * 2
        return text[:char_limit] if len(text) > char_limit else text

    tokens = encoder.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated_tokens = tokens[:max_tokens]
    return encoder.decode(truncated_tokens)


def split_text_by_tokens(text: str, chunk_size: int = 60000,
                         overlap: int = 500, model: str = "deepseek-chat") -> List[str]:
    """
    按 Token 数分片长文本，支持重叠以保持上下文连续性。

    Args:
        text: 待分片文本
        chunk_size: 单片 Token 数（默认 60k，预留 prompt 与响应空间）
        overlap: 相邻片段重叠 Token 数
        model: 模型名

    Returns:
        分片后的文本列表
    """
    if not text:
        return []
    total = count_tokens(text, model)
    if total <= chunk_size:
        return [text]

    encoder = get_encoder(model)
    if encoder is None:
        # 兜底：按字符分片
        char_size = chunk_size * 2
        char_overlap = overlap * 2
        chunks = []
        start = 0
        while start < len(text):
            end = start + char_size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - char_overlap
        return chunks

    tokens = encoder.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunks.append(encoder.decode(chunk_tokens))
        if end >= len(tokens):
            break
        start = end - overlap
    return chunks


def estimate_request_tokens(system_prompt: str, user_content: str,
                            model: str = "deepseek-chat") -> int:
    """估算一次请求的总 Token 数"""
    # 经验值：system + user + 对话框架开销约 50 token
    overhead = 50
    return count_tokens(system_prompt, model) + count_tokens(user_content, model) + overhead


def build_safe_payload(system_prompt: str, user_content: str,
                       max_context: int = USABLE_MAX_TOKENS,
                       model: str = "deepseek-chat") -> dict:
    """
    构建安全的请求 payload：若 user_content 超限则自动截断，
    返回 {content, truncated, original_tokens, used_tokens}
    """
    sys_tokens = count_tokens(system_prompt, model)
    available = max_context - sys_tokens - SAFE_RESERVE_TOKENS
    if available <= 0:
        # system prompt 自身就超限，需外部处理
        return {
            "content": user_content,
            "truncated": False,
            "original_tokens": count_tokens(user_content, model),
            "used_tokens": count_tokens(user_content, model),
            "warning": "system prompt 过长，请精简后重试",
        }

    original_tokens = count_tokens(user_content, model)
    if original_tokens <= available:
        return {
            "content": user_content,
            "truncated": False,
            "original_tokens": original_tokens,
            "used_tokens": original_tokens,
        }

    truncated = truncate_to_tokens(user_content, available, model)
    return {
        "content": truncated,
        "truncated": True,
        "original_tokens": original_tokens,
        "used_tokens": available,
        "warning": f"内容已自动截断（{original_tokens} → {available} tokens）",
    }
