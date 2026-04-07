# TripStar 高德地图 API 使用指南

本文档详细介绍 TripStar 项目如何调用高德地图 API 来实现景点、酒店、餐厅等兴趣点（POI）的搜索功能。

---

## 目录
1. [项目使用的 API 概览](#1-项目使用的-api-概览)
2. [高德 API 基础配置](#2-高德-api-基础配置)
3. [POI 搜索功能实现](#3-poi-搜索功能实现)
4. [天气查询功能实现](#4-天气查询功能实现)
5. [路线规划功能实现](#5-路线规划功能实现)
6. [完整代码实现示例](#6-完整代码实现示例)
7. [其他项目复用指南](#7-其他项目复用指南)

---

## 1. 项目使用的 API 概览

| API 端点 | 功能 | 高德文档 |
|---------|------|----------|
| `/v3/place/text` | POI搜索（景点、酒店、餐厅等） | [Place Text API](https://lbs.amap.com/api/webservice/guide/search/text) |
| `/v3/weather/weatherInfo` | 天气查询 | [Weather API](https://lbs.amap.com/api/webservice/guide/weather) |
| `/v3/geocode/geo` | 地理编码（地址转坐标） | [Geocode API](https://lbs.amap.com/api/webservice/guide/geocoding) |
| `/v3/direction/walking` | 步行路线规划 | [Direction API](https://lbs.amap.com/api/webservice/guide/direction) |
| `/v3/direction/driving` | 驾车路线规划 | 同上 |
| `/v3/direction/transit` | 公交路线规划 | 同上 |

### 基础配置
- **基础URL**: `https://restapi.amap.com/v3`
- **API Key**: 需要在高德开放平台申请 Web 服务 API Key

---

## 2. 高德 API 基础配置

### 2.1 申请 API Key

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册/登录账号
3. 创建应用 → 获取 Web 服务 API Key
4. 在应用设置中启用需要的服务（如：搜索服务、天气服务、路径规划服务等）

### 2.2 环境变量配置

```bash
# Backend (.env)
VITE_AMAP_WEB_KEY=你的高德API密钥

# Frontend (.env)
VITE_AMAP_WEB_KEY=你的高德API密钥
VITE_AMAP_WEB_JS_KEY=你的高德JS API密钥
```

### 2.3 Python 请求封装

```python
import requests

class AmapService:
    BASE_URL = "https://restapi.amap.com/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def _request(self, endpoint: str, params: dict) -> dict:
        """发送API请求"""
        params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        return response.json()
```

---

## 3. POI 搜索功能实现

### 3.1 接口信息

**请求地址**: `GET /v3/place/text`

**请求参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| key | 是 | string | 高德API Key |
| keywords | 是 | string | 搜索关键词 |
| city | 是 | string | 搜索城市名称 |
| citylimit | 否 | boolean | 是否限制在城市范围内，默认true |
| offset | 否 | int | 每页返回数量，默认20 |
| page | 否 | int | 页码，默认1 |
| types | 否 | string | POI类型代码 |
| extensions | 否 | string | 返回格式，all返回详细信息 |

### 3.2 常用 POI 类型代码

| 类型 | 代码 | 说明 |
|------|------|------|
| 景点 | 110000 | 风景名胜 |
| 酒店 | 100000 | 住宿服务 |
| 餐厅 | 050000 | 餐饮服务 |
| 商场 | 060000 | 购物服务 |
| 地铁站 | 150500 | 交通设施 |
| 机场 | 150600 | 交通设施 |
| 火车站 | 150100 | 交通设施 |

### 3.3 返回字段说明

```json
{
  "status": "1",
  "count": 20,
  "pois": [
    {
      "id": "POI唯一ID",
      "name": "名称",
      "type": "类型",
      "typecode": "类型代码",
      "address": "地址",
      "location": "经度,纬度",
      "tel": "电话",
      "pname": "省份",
      "cityname": "城市",
      "adname": "区县"
    }
  ]
}
```

### 3.4 代码实现

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Location:
    longitude: float
    latitude: float

@dataclass
class POIInfo:
    id: str
    name: str
    type: str
    address: str
    location: Location
    tel: Optional[str] = None

class AmapService:
    BASE_URL = "https://restapi.amap.com/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def _request(self, endpoint: str, params: dict) -> dict:
        params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        return requests.get(url, params=params, timeout=10).json()
    
    def search_poi(
        self, 
        keywords: str, 
        city: str, 
        citylimit: bool = True,
        offset: int = 20,
        poi_type: str = ""
    ) -> List[POIInfo]:
        """
        搜索POI
        
        Args:
            keywords: 搜索关键词，如"景点"、"酒店"、"餐厅"
            city: 城市名称，如"北京"
            citylimit: 是否限制在城市范围内
            offset: 返回数量
            poi_type: POI类型代码，如"110000"表示景点
        
        Returns:
            POI信息列表
        """
        params = {
            "keywords": keywords,
            "city": city,
            "citylimit": "true" if citylimit else "false",
            "offset": offset,
            "page": 1,
            "extensions": "all"
        }
        if poi_type:
            params["types"] = poi_type
        
        data = self._request("place/text", params)
        
        pois = []
        if data.get("status") == "1" and data.get("pois"):
            for poi in data["pois"]:
                # 解析经纬度 "116.397128,39.916527"
                location = poi.get("location", "")
                lng, lat = 0.0, 0.0
                if location:
                    parts = location.split(",")
                    if len(parts) == 2:
                        lng = float(parts[0])
                        lat = float(parts[1])
                
                pois.append(POIInfo(
                    id=poi.get("id", ""),
                    name=poi.get("name", ""),
                    type=poi.get("type", ""),
                    address=poi.get("address", poi.get("city", "")),
                    location=Location(longitude=lng, latitude=lat),
                    tel=poi.get("tel") if poi.get("tel") else None
                ))
        
        return pois

# 使用示例
service = AmapService("你的API_KEY")

# 搜索景点
attractions = service.search_poi("景点", "北京", poi_type="110000")
for poi in attractions:
    print(f"{poi.name} - {poi.address} ({poi.location.longitude}, {poi.location.latitude})")

# 搜索酒店
hotels = service.search_poi("酒店", "北京", poi_type="100000")

# 搜索餐厅
restaurants = service.search_poi("餐厅", "北京", poi_type="050000")
```

---

## 4. 天气查询功能实现

### 4.1 接口信息

**请求地址**: `GET /v3/weather/weatherInfo`

**请求参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| key | 是 | string | 高德API Key |
| city | 是 | string | 城市编码（如 110000）或城市名称 |
| extensions | 否 | string | base=实况天气，all=预报天气 |
| output | 否 | string | 返回格式，JSON或XML |

### 4.2 城市编码获取

由于天气API需要城市编码（adcode），需要先通过地理编码API获取：

```python
def _get_city_adcode(self, city: str) -> Optional[str]:
    """获取城市编码"""
    # 常见城市映射
    city_map = {
        "北京": "110000", "上海": "310000", "广州": "440100",
        "深圳": "440300", "杭州": "330100", "成都": "510100",
        "重庆": "500000", "武汉": "420100", "西安": "610100",
        "南京": "320100", "苏州": "320500", "天津": "120000",
    }
    
    if city in city_map:
        return city_map[city]
    
    # 通过地理编码API获取
    params = {"address": city}
    data = self._request("geocode/geo", params)
    
    if data.get("status") == "1" and data.get("geocodes"):
        return data["geocodes"][0].get("adcode")
    
    return None
```

### 4.3 代码实现

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class WeatherInfo:
    date: str
    day_weather: str
    night_weather: str
    day_temp: str
    night_temp: str
    wind_direction: str
    wind_power: str

def get_weather(self, city: str) -> List[WeatherInfo]:
    """查询天气"""
    # 获取城市编码
    adcode = self._get_city_adcode(city)
    if not adcode:
        return []
    
    params = {
        "city": adcode,
        "extensions": "base",
        "output": "json"
    }
    
    data = self._request("weather/weatherInfo", params)
    
    weather_list = []
    if data.get("status") == "1" and data.get("lives"):
        today = datetime.now().strftime("%Y-%m-%d")
        
        for live in data["lives"]:
            weather_list.append(WeatherInfo(
                date=today,
                day_weather=live.get("weather", ""),
                night_weather="",
                day_temp=live.get("temperature", "0"),
                night_temp="0",
                wind_direction=live.get("winddirection", ""),
                wind_power=live.get("windpower", "")
            ))
    
    return weather_list

# 使用示例
weather = service.get_weather("北京")
for w in weather:
    print(f"{w.date}: {w.day_weather}, {w.day_temp}°C")
```

---

## 5. 路线规划功能实现

### 5.1 接口信息

**请求地址**: 
- 步行: `GET /v3/direction/walking`
- 驾车: `GET /v3/direction/driving`
- 公交: `GET /v3/direction/transit`

**请求参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| key | 是 | string | 高德API Key |
| origin | 是 | string | 起点经纬度，如 "116.397128,39.916527" |
| destination | 是 | string | 终点经纬度 |
| strategy | 否 | string | 路径策略（驾车） |
| city | 否 | string | 城市（公交） |

### 5.2 代码实现

```python
def plan_route(
    self,
    origin_lng: float,
    origin_lat: float,
    destination_lng: float,
    destination_lat: float,
    route_type: str = "walking"
) -> dict:
    """规划路线
    
    Args:
        origin_lng: 起点经度
        origin_lat: 起点纬度
        destination_lng: 终点经度
        destination_lat: 终点纬度
        route_type: walking/driving/transit
    
    Returns:
        路线信息
    """
    endpoint_map = {
        "walking": "direction/walking",
        "driving": "direction/driving",
        "transit": "direction/transit"
    }
    
    endpoint = endpoint_map.get(route_type, "direction/walking")
    params = {
        "origin": f"{origin_lng},{origin_lat}",
        "destination": f"{destination_lng},{destination_lat}"
    }
    
    return self._request(endpoint, params)

# 使用示例
route = service.plan_route(
    origin_lng=116.397128,
    origin_lat=39.916527,
    destination_lng=116.427428,
    destination_lat=39.92323,
    route_type="driving"
)
```

---

## 6. 完整代码实现示例

```python
"""
高德地图服务封装 - 完整实现
适用于任何Python项目的POI搜索功能
"""

import requests
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Location:
    """地理坐标"""
    longitude: float
    latitude: float


@dataclass
class POIInfo:
    """POI信息"""
    id: str
    name: str
    type: str
    address: str
    location: Location
    tel: Optional[str] = None


@dataclass
class WeatherInfo:
    """天气信息"""
    date: str
    day_weather: str
    night_weather: str
    day_temp: str
    night_temp: str
    wind_direction: str
    wind_power: str


class AmapService:
    """高德地图服务封装类"""
    
    BASE_URL = "https://restapi.amap.com/v3"
    
    # 常用城市编码映射
    CITY_ADCODE_MAP = {
        "北京": "110000", "上海": "310000", "广州": "440100",
        "深圳": "440300", "杭州": "330100", "成都": "510100",
        "重庆": "500000", "武汉": "420100", "西安": "610100",
        "南京": "320100", "苏州": "320500", "天津": "120000",
        "青岛": "370200", "长沙": "430100", "郑州": "410100",
        "沈阳": "210100", "大连": "210200", "厦门": "350200",
        "昆明": "530100", "哈尔滨": "230100"
    }
    
    # POI类型代码
    POI_TYPES = {
        "景点": "110000",
        "酒店": "100000",
        "餐厅": "050000",
        "商场": "060000",
        "地铁站": "150500",
        "机场": "150600",
        "火车站": "150100"
    }
    
    def __init__(self, api_key: str):
        """初始化服务
        
        Args:
            api_key: 高德Web服务API Key
        """
        if not api_key:
            raise ValueError("高德地图API Key未配置")
        self.api_key = api_key
    
    def _request(self, endpoint: str, params: dict) -> dict:
        """发送API请求"""
        params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    
    def search_poi(
        self,
        keywords: str,
        city: str,
        citylimit: bool = True,
        offset: int = 20,
        poi_type: str = ""
    ) -> List[POIInfo]:
        """
        搜索POI（景点、酒店、餐厅等）
        
        Args:
            keywords: 搜索关键词
            city: 城市名称
            citylimit: 是否限制在城市范围内
            offset: 返回数量
            poi_type: POI类型代码，如"110000"(景点)、"100000"(酒店)
        
        Returns:
            POI信息列表
        """
        params = {
            "keywords": keywords,
            "city": city,
            "citylimit": "true" if citylimit else "false",
            "offset": offset,
            "page": 1,
            "extensions": "all"
        }
        if poi_type:
            params["types"] = poi_type
        
        data = self._request("place/text", params)
        
        pois = []
        if data.get("status") == "1" and data.get("pois"):
            for poi in data["pois"]:
                location = poi.get("location", "")
                lng, lat = 0.0, 0.0
                if location:
                    parts = location.split(",")
                    if len(parts) == 2:
                        lng, lat = float(parts[0]), float(parts[1])
                
                pois.append(POIInfo(
                    id=poi.get("id", ""),
                    name=poi.get("name", ""),
                    type=poi.get("type", ""),
                    address=poi.get("address", ""),
                    location=Location(longitude=lng, latitude=lat),
                    tel=poi.get("tel") if poi.get("tel") else None
                ))
        
        return pois
    
    def search_attractions(self, city: str, keywords: str = "景点") -> List[POIInfo]:
        """搜索景点"""
        return self.search_poi(keywords, city, poi_type=self.POI_TYPES["景点"])
    
    def search_hotels(self, city: str, keywords: str = "酒店") -> List[POIInfo]:
        """搜索酒店"""
        return self.search_poi(keywords, city, poi_type=self.POI_TYPES["酒店"])
    
    def search_restaurants(self, city: str, keywords: str = "餐厅") -> List[POIInfo]:
        """搜索餐厅"""
        return self.search_poi(keywords, city, poi_type=self.POI_TYPES["餐厅"])
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """查询天气"""
        adcode = self._get_city_adcode(city)
        if not adcode:
            return []
        
        params = {
            "city": adcode,
            "extensions": "base",
            "output": "json"
        }
        
        data = self._request("weather/weatherInfo", params)
        
        weather_list = []
        if data.get("status") == "1" and data.get("lives"):
            today = datetime.now().strftime("%Y-%m-%d")
            for live in data["lives"]:
                weather_list.append(WeatherInfo(
                    date=today,
                    day_weather=live.get("weather", ""),
                    night_weather="",
                    day_temp=live.get("temperature", "0"),
                    night_temp="0",
                    wind_direction=live.get("winddirection", ""),
                    wind_power=live.get("windpower", "")
                ))
        
        return weather_list
    
    def _get_city_adcode(self, city: str) -> Optional[str]:
        """获取城市编码"""
        if city in self.CITY_ADCODE_MAP:
            return self.CITY_ADCODE_MAP[city]
        
        params = {"address": city}
        data = self._request("geocode/geo", params)
        
        if data.get("status") == "1" and data.get("geocodes"):
            return data["geocodes"][0].get("adcode")
        
        return None
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """地理编码（地址转坐标）"""
        params = {"address": address}
        if city:
            params["city"] = city
            params["citylimit"] = "true"
        
        data = self._request("geocode/geo", params)
        
        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0].get("location", "")
            if location:
                parts = location.split(",")
                if len(parts) == 2:
                    return Location(longitude=float(parts[0]), latitude=float(parts[1]))
        
        return None
    
    def plan_route(
        self,
        origin_lng: float,
        origin_lat: float,
        destination_lng: float,
        destination_lat: float,
        route_type: str = "walking"
    ) -> dict:
        """规划路线
        
        Args:
            origin_lng: 起点经度
            origin_lat: 起点纬度
            destination_lng: 终点经度
            destination_lat: 终点纬度
            route_type: walking/driving/transit
        
        Returns:
            路线信息
        """
        endpoint_map = {
            "walking": "direction/walking",
            "driving": "direction/driving",
            "transit": "direction/transit"
        }
        
        endpoint = endpoint_map.get(route_type, "direction/walking")
        params = {
            "origin": f"{origin_lng},{origin_lat}",
            "destination": f"{destination_lng},{destination_lat}"
        }
        
        return self._request(endpoint, params)


# ============ 使用示例 ============

if __name__ == "__main__":
    # 初始化服务（替换为你的API Key）
    service = AmapService("你的高德API Key")
    
    # 1. 搜索景点
    print("=== 搜索北京景点 ===")
    attractions = service.search_attractions("北京")
    for a in attractions[:5]:
        print(f"  {a.name} - {a.address}")
    
    # 2. 搜索酒店
    print("\n=== 搜索北京酒店 ===")
    hotels = service.search_hotels("北京")
    for h in hotels[:5]:
        print(f"  {h.name} - {h.address}")
    
    # 3. 搜索餐厅
    print("\n=== 搜索北京餐厅 ===")
    restaurants = service.search_restaurants("北京")
    for r in restaurants[:5]:
        print(f"  {r.name} - {r.address}")
    
    # 4. 查询天气
    print("\n=== 查询北京天气 ===")
    weather = service.get_weather("北京")
    for w in weather:
        print(f"  {w.date}: {w.day_weather}, {w.day_temp}°C")
    
    # 5. 地理编码
    print("\n=== 地理编码 ===")
    location = service.geocode("故宫", "北京")
    if location:
        print(f"  故宫坐标: {location.longitude}, {location.latitude}")
```

---

## 7. 其他项目复用指南

### 7.1 快速集成步骤

1. **申请高德API Key**
   - 访问 https://lbs.amap.com/
   - 创建应用，获取 Web 服务 API Key
   - 在控制台启用"搜索服务"、"天气服务"等

2. **安装依赖**
   ```bash
   pip install requests
   ```

3. **复制服务类**
   - 复制上面的 `AmapService` 类到你的项目中
   - 初始化时传入你的 API Key

4. **调用示例**
   ```python
   from amap_service import AmapService
   
   service = AmapService("你的API_KEY")
   
   # 搜索景点
   attractions = service.search_poi("景点", "杭州", poi_type="110000")
   
   # 搜索酒店  
   hotels = service.search_poi("酒店", "杭州", poi_type="100000")
   
   # 搜索餐厅
   restaurants = service.search_poi("餐厅", "杭州", poi_type="050000")
   ```

### 7.2 注意事项

1. **API配额**: 免费账户有每日调用配额限制，超出后会返回错误
2. **城市编码**: 天气查询需要城市编码，代码中已包含常见城市映射
3. **经纬度格式**: 高德返回格式为 `经度,纬度`（注意顺序）
4. **错误处理**: 建议添加异常捕获处理网络超时等情况

### 7.3 常见问题

**Q: 搜索结果为空怎么办？**
- 检查 API Key 是否正确
- 确认城市名称是否正确（如"北京"不是"北京市"）
- 检查是否已启用搜索服务

**Q: 天气查询失败怎么办？**
- 确认城市名称在常见城市映射中，或通过地理编码获取 adcode
- 检查是否已启用天气服务

**Q: 如何获取更多信息？**
- 参考 [高德开放平台文档](https://lbs.amap.com/api/webservice/guide/search-new)