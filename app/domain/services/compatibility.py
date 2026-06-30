"""
兼容性评分计算
基于多维度匹配算法的 100 分制评分系统
"""
import math
from typing import Optional


INTEREST_WEIGHT = 30      # 兴趣爱好匹配权重
LOOKING_FOR_WEIGHT = 20   # 交友目的匹配权重
PERSONALITY_WEIGHT = 30   # 性格测试匹配权重
VALUE_WEIGHT = 20         # 价值观匹配权重


def _jaccard(set_a: set, set_b: set) -> float:
    """计算两个集合的 Jaccard 相似度"""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _cosine_sim(vec_a: dict, vec_b: dict) -> float:
    """计算两个向量的余弦相似度"""
    all_keys = set(vec_a.keys()) | set(vec_b.keys())
    if not all_keys:
        return 0.0

    def safe_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    dot = sum(safe_float(vec_a.get(k, 0)) * safe_float(vec_b.get(k, 0)) for k in all_keys)
    norm_a = math.sqrt(sum(safe_float(v) ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(safe_float(v) ** 2 for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def calculate_compatibility(user1: dict, user2: dict) -> int:
    """
    计算两个用户的兼容性评分。
    
    评分维度（总分 100）：
    - 兴趣爱好匹配：30 分
    - 交友目的匹配：20 分
    - 性格测试匹配：30 分
    - 价值观匹配：20 分
    
    Args:
        user1, user2: 用户资料字典
    
    Returns:
        int: 兼容性评分 (0-100)
    """
    score = 0.0

    # 1. 兴趣爱好匹配 (30 分)
    interests1 = set(user1.get("interests", []))
    interests2 = set(user2.get("interests", []))
    score += _jaccard(interests1, interests2) * INTEREST_WEIGHT

    # 2. 交友目的匹配 (20 分)
    looking1 = user1.get("looking_for", "")
    looking2 = user2.get("looking_for", "")
    if looking1 and looking2 and looking1 == looking2:
        score += LOOKING_FOR_WEIGHT
    elif looking1 and looking2:
        score += LOOKING_FOR_WEIGHT * 0.3  # 部分匹配

    # 3. 性格测试匹配 (30 分)
    personality1 = user1.get("personality_quiz", {})
    personality2 = user2.get("personality_quiz", {})
    if personality1 and personality2:
        score += _cosine_sim(personality1, personality2) * PERSONALITY_WEIGHT

    # 4. 价值观匹配 (20 分)
    values1 = user1.get("values", {})
    values2 = user2.get("values", {})
    if values1 and values2:
        score += _cosine_sim(values1, values2) * VALUE_WEIGHT

    return min(round(score), 100)


def get_shared_tags(user1: dict, user2: dict) -> list:
    """获取两个用户共享的兴趣标签"""
    interests1 = set(user1.get("interests", []))
    interests2 = set(user2.get("interests", []))
    return sorted(list(interests1 & interests2))


def get_shared_values(user1: dict, user2: dict) -> list:
    """获取两个用户共享的价值观"""
    values1 = user1.get("values", {})
    values2 = user2.get("values", {})
    shared = []
    for key in set(values1.keys()) & set(values2.keys()):
        if values1[key] == values2[key]:
            shared.append(key)
    return sorted(shared)


def normalise(score: float, min_val: float = 0, max_val: float = 100) -> float:
    """标准化分数到 0-1 范围"""
    if max_val - min_val == 0:
        return 0.5
    return (score - min_val) / (max_val - min_val)
