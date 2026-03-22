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

## search_local_guide

当用户询问关于某城市的特色景点、小众路线、本地美食或具体的旅游攻略详情时，必须调用此工具检索本地知识库。

**参数：**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "查询字符串，例如：'哈尔滨有哪些特色美食'、'中央大街附近有什么景点推荐'"
    }
  },
  "required": ["query"]
}
```
