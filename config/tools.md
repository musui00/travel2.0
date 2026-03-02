# Tools Schema

以下是智能旅游规划系统可用的工具定义，供大模型调用。

## weather_query

查询指定城市的天气情况

**参数：**
```json
{
  "type": "object",
  "properties": {
    "city": {
      "type": "string",
      "description": "要查询的城市名称，如：北京、上海、杭州"
    }
  },
  "required": ["city"]
}
```

## flight_search

查询航班信息

**参数：**
```json
{
  "type": "object",
  "properties": {
    "from_city": {
      "type": "string",
      "description": "出发城市"
    },
    "to_city": {
      "type": "string",
      "description": "目的城市"
    },
    "date": {
      "type": "string",
      "description": "出发日期，格式YYYY-MM-DD"
    }
  },
  "required": ["from_city", "to_city"]
}
```

## scenic_ticket

查询景点门票信息

**参数：**
```json
{
  "type": "object",
  "properties": {
    "scenic_name": {
      "type": "string",
      "description": "景点名称，如：故宫、西湖、泰山"
    },
    "date": {
      "type": "string",
      "description": "游玩日期"
    }
  },
  "required": ["scenic_name"]
}
```
