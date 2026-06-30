"""
Haversine 距离计算 —— 领域服务（无 I/O 依赖）
来源：参考 Connectly (dating-platform-api) 的 domain/services/ 设计
许可证：MIT（算法公式为数学公共知识）
"""
import math

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine 公式计算两点间的地表距离。

    Args:
        lat1, lon1: 用户坐标
        lat2, lon2: 目标坐标

    Returns:
        距离（公里）
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lon: float, radius_km: float) -> dict:
    """
    计算给定坐标在指定半径范围内的经纬度边界框。

    用于数据库查询的初步地理过滤。

    Returns:
        {"min_lat", "max_lat", "min_lon", "max_lon"}
    """
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))

    return {
        "min_lat": lat - lat_delta,
        "max_lat": lat + lat_delta,
        "min_lon": lon - lon_delta,
        "max_lon": lon + lon_delta,
    }
