"""
Haversine 距离计算
用于计算地球表面两点之间的最短距离（大圆距离）
"""
import math

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine 公式计算两点间的球面距离。
    
    Args:
        lat1, lon1: 第一个点的纬度和经度（度）
        lat2, lon2: 第二个点的纬度和经度（度）
    
    Returns:
        float: 两点间的距离（公里）
    """
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lon: float, radius_km: float) -> dict:
    """
    计算给定中心点和半径的边界框。
    
    Args:
        lat: 中心点纬度
        lon: 中心点经度
        radius_km: 半径（公里）
    
    Returns:
        dict: 包含 min_lat, max_lat, min_lon, max_lon 的边界
    """
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    angular_radius = radius_km / EARTH_RADIUS_KM

    min_lat = lat_r - angular_radius
    max_lat = lat_r + angular_radius

    delta_lon = math.asin(math.sin(angular_radius) / math.cos(lat_r))
    min_lon = lon_r - delta_lon
    max_lon = lon_r + delta_lon

    return {
        "min_lat": math.degrees(min_lat),
        "max_lat": math.degrees(max_lat),
        "min_lon": math.degrees(min_lon),
        "max_lon": math.degrees(max_lon),
    }
