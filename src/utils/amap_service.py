"""
高德地图服务封装
提供 POI 搜索、天气查询、路线规划等功能
"""

import requests
from dataclasses import dataclass
from typing import List, Optional

from src.utils.logger import logger


@dataclass
class Location:
    """地理坐标"""

    longitude: float
    latitude: float


@dataclass
class POIInfo:
    """POI 信息"""

    id: str
    name: str
    type: str
    typecode: str
    address: str
    location: Location
    tel: Optional[str] = None
    pname: Optional[str] = None
    cityname: Optional[str] = None
    adname: Optional[str] = None


class AmapService:
    """高德地图服务封装类"""

    BASE_URL = "https://restapi.amap.com/v3"

    # 常用城市编码映射
    CITY_ADCODE_MAP = {
        "北京": "110000",
        "上海": "310000",
        "广州": "440100",
        "深圳": "440300",
        "杭州": "330100",
        "成都": "510100",
        "重庆": "500000",
        "武汉": "420100",
        "西安": "610100",
        "南京": "320100",
        "苏州": "320500",
        "天津": "120000",
        "青岛": "370200",
        "长沙": "430100",
        "郑州": "410100",
        "沈阳": "210100",
        "大连": "210200",
        "厦门": "350200",
        "昆明": "530100",
        "哈尔滨": "230100",
    }

    # POI 类型代码
    POI_TYPES = {
        "景点": "110000",
        "酒店": "100000",
        "餐厅": "050000",
        "商场": "060000",
        "地铁站": "150500",
        "机场": "150600",
        "火车站": "150100",
    }

    def __init__(self, api_key: str):
        """初始化服务

        Args:
            api_key: 高德 Web 服务 API Key
        """
        if not api_key:
            raise ValueError("高德地图 API Key 未配置")
        self.api_key = api_key

    def _request(self, endpoint: str, params: dict) -> dict:
        """发送 API 请求

        Args:
            endpoint: API 端点
            params: 请求参数

        Returns:
            响应数据
        """
        params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get("status") != "1":
                logger.error(f"高德 API 调用失败: {data}")
                return {}
            return data
        except Exception as e:
            logger.error(f"高德 API 请求异常: {e}")
            return {}

    def search_poi(
        self,
        keywords: str,
        city: str,
        citylimit: bool = True,
        offset: int = 20,
        page: int = 1,
        poi_type: str = "",
    ) -> List[POIInfo]:
        """搜索 POI（景点、酒店、餐厅等）

        Args:
            keywords: 搜索关键词
            city: 城市名称
            citylimit: 是否限制在城市范围内
            offset: 返回数量
            page: 页码
            poi_type: POI 类型代码

        Returns:
            POI 信息列表
        """
        params = {
            "keywords": keywords,
            "city": city,
            "citylimit": "true" if citylimit else "false",
            "offset": offset,
            "page": page,
            "extensions": "all",
        }
        if poi_type:
            params["types"] = poi_type

        data = self._request("place/text", params)

        pois = []
        if data.get("pois"):
            for poi in data["pois"]:
                location = poi.get("location", "")
                lng, lat = 0.0, 0.0
                if location:
                    parts = location.split(",")
                    if len(parts) == 2:
                        lng, lat = float(parts[0]), float(parts[1])

                pois.append(
                    POIInfo(
                        id=poi.get("id", ""),
                        name=poi.get("name", ""),
                        type=poi.get("type", ""),
                        typecode=poi.get("typecode", ""),
                        address=poi.get("address", ""),
                        location=Location(longitude=lng, latitude=lat),
                        tel=poi.get("tel") if poi.get("tel") else None,
                        pname=poi.get("pname"),
                        cityname=poi.get("cityname"),
                        adname=poi.get("adname"),
                    )
                )

        logger.info(f"高德 POI 搜索: {keywords} in {city}, 返回 {len(pois)} 条结果")
        return pois

    def search_attractions(
        self, city: str, keywords: str = "景点", limit: int = 10
    ) -> List[POIInfo]:
        """搜索景点

        Args:
            city: 城市名称
            keywords: 关键词
            limit: 返回数量

        Returns:
            景点列表
        """
        pois = self.search_poi(
            keywords, city, poi_type=self.POI_TYPES["景点"], offset=limit
        )
        return pois

    def search_hotels(
        self, city: str, keywords: str = "酒店", limit: int = 10
    ) -> List[POIInfo]:
        """搜索酒店

        Args:
            city: 城市名称
            keywords: 关键词
            limit: 返回数量

        Returns:
            酒店列表
        """
        pois = self.search_poi(
            keywords, city, poi_type=self.POI_TYPES["酒店"], offset=limit
        )
        return pois

    def search_restaurants(
        self, city: str, keywords: str = "餐厅", cuisine: str = "", limit: int = 10
    ) -> List[POIInfo]:
        """搜索餐厅

        Args:
            city: 城市名称
            keywords: 关键词
            cuisine: 菜系（如川菜、火锅等）
            limit: 返回数量

        Returns:
            餐厅列表
        """
        search_keywords = f"{cuisine}{keywords}" if cuisine else keywords
        pois = self.search_poi(
            search_keywords, city, poi_type=self.POI_TYPES["餐厅"], offset=limit
        )
        return pois

    def get_weather(self, city: str) -> dict:
        """查询天气

        Args:
            city: 城市名称

        Returns:
            天气信息字典
        """
        adcode = self._get_city_adcode(city)
        if not adcode:
            logger.warning(f"无法获取城市编码: {city}")
            return {}

        params = {"city": adcode, "extensions": "base", "output": "json"}
        data = self._request("weather/weatherInfo", params)

        if data.get("lives"):
            weather = data["lives"][0]
            logger.info(
                f"查询天气: {city}, 天气={weather.get('weather')}, 温度={weather.get('temperature')}"
            )
            return {
                "city": weather.get("city", ""),
                "weather": weather.get("weather", ""),
                "temperature": weather.get("temperature", ""),
                "wind_direction": weather.get("winddirection", ""),
                "wind_power": weather.get("windpower", ""),
                "humidity": weather.get("humidity", ""),
            }
        return {}

    def _get_city_adcode(self, city: str) -> Optional[str]:
        """获取城市编码

        Args:
            city: 城市名称

        Returns:
            城市编码
        """
        if city in self.CITY_ADCODE_MAP:
            return self.CITY_ADCODE_MAP[city]

        # 通过地理编码 API 获取
        params = {"address": city}
        data = self._request("geocode/geo", params)

        if data.get("geocodes"):
            return data["geocodes"][0].get("adcode")

        return None

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """地理编码（地址转坐标）

        Args:
            address: 地址
            city: 城市名称

        Returns:
            坐标信息
        """
        params = {"address": address}
        if city:
            params["city"] = city
            params["citylimit"] = "true"

        data = self._request("geocode/geo", params)

        if data.get("geocodes"):
            location = data["geocodes"][0].get("location", "")
            if location:
                parts = location.split(",")
                if len(parts) == 2:
                    logger.info(f"地理编码: {address} -> {location}")
                    return Location(longitude=float(parts[0]), latitude=float(parts[1]))

        return None


# 全局服务实例（延迟初始化）
_amap_service: Optional[AmapService] = None


def get_amap_service(api_key: Optional[str] = None) -> Optional[AmapService]:
    """获取高德地图服务实例

    Args:
        api_key: API Key，默认从配置读取

    Returns:
        AmapService 实例
    """
    global _amap_service

    if _amap_service is None:
        if api_key is None:
            # 从配置读取
            try:
                import yaml

                with open("config/config.yaml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                api_key = config.get("AMAP_API_KEY", "")
            except Exception:
                pass

        if api_key:
            _amap_service = AmapService(api_key)
            logger.info("高德地图服务初始化成功")

    return _amap_service
