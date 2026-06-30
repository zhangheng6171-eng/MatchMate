"""
兼容性匹配算法 —— 领域服务
来源：参考 MIIRA-matchmaking 的 compatibilityService.js
许可：MIT（算法逻辑适配后的原创实现）
"""
from typing import Optional


def normalise(arr: Optional[list]) -> list:
    """标准化数组：去空、去重、小写化"""
    if not arr or not isinstance(arr, list):
        return []
    return list({s.strip().lower() for s in arr if s and s.strip()})


def calculate_compatibility(user1: dict, user2: dict) -> int:
    """
    计算两个用户之间的兼容性评分（0-100）。

    评分维度：
    - 共享兴趣 + 爱好：30 分
    - 相同的"寻找对象"目标：20 分
    - 人格测评对齐：30 分
    - 共享核心价值观：20 分

    Args:
        user1: 用户1的完整资料 dict
        user2: 用户2的完整资料 dict

    Returns:
        0-100 的整数评分
    """
    score = 0.0

    # --- 1. 共享兴趣 + 爱好（30 分）---
    interests1 = normalise(user1.get("interests", []))
    interests2 = normalise(user2.get("interests", []))
    hobbies1 = normalise(user1.get("hobbies", []))
    hobbies2 = normalise(user2.get("hobbies", []))

    tags1 = list({*interests1, *hobbies1})
    tags2 = list({*interests2, *hobbies2})
    shared_tags = [t for t in tags1 if t in tags2]
    max_tags = max(len(tags1), len(tags2), 1)

    score += min((len(shared_tags) / max_tags) * 30 * 2, 30)

    # --- 2. 寻找对象目标（20 分）---
    looking_for_1 = user1.get("looking_for")
    looking_for_2 = user2.get("looking_for")
    if looking_for_1 and looking_for_2:
        score += 20 if looking_for_1 == looking_for_2 else 5
    else:
        score += 10  # 未设置时给默认分

    # --- 3. 人格测评对齐（30 分）---
    quiz1 = user1.get("personality_quiz") or {}
    quiz2 = user2.get("personality_quiz") or {}
    keys = [f"q{i}" for i in range(1, 16)]  # q1 ~ q15

    answered = 0
    matched = 0
    for k in keys:
        if quiz1.get(k) and quiz2.get(k):
            answered += 1
            if quiz1[k] == quiz2[k]:
                matched += 1

    score += (matched / answered) * 30 if answered > 0 else 15

    # --- 4. 共享核心价值观（20 分）---
    values1 = normalise(user1.get("values", []))
    values2 = normalise(user2.get("values", []))
    shared_values = [v for v in values1 if v in values2]
    max_values = max(len(values1), len(values2), 1)

    score += min((len(shared_values) / max_values) * 20 * 2, 20)

    return min(round(score), 100)


def get_shared_tags(user1: dict, user2: dict) -> list:
    """获取两个用户共享的兴趣/爱好标签（用于「为什么匹配」展示）"""
    interests1 = normalise(user1.get("interests", []))
    interests2 = normalise(user2.get("interests", []))
    hobbies1 = normalise(user1.get("hobbies", []))
    hobbies2 = normalise(user2.get("hobbies", []))

    tags1 = list({*interests1, *hobbies1})
    tags2 = list({*interests2, *hobbies2})
    return [t for t in tags1 if t in tags2]


def get_shared_values(user1: dict, user2: dict) -> list:
    """获取两个用户共享的核心价值观"""
    values1 = normalise(user1.get("values", []))
    values2 = normalise(user2.get("values", []))
    return [v for v in values1 if v in values2]
