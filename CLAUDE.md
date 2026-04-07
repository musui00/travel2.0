# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基于 ModelScope API 的智能旅游规划系统，采用 **LangGraph Multi-Agent 架构**。

## Architecture

### LangGraph Multi-Agent 架构

```
┌─────────────────────────────────────────────────────┐
│                 Supervisor                         │
│         (主路由 Agent，协调子 Agent)            │
└──────────────┬──────────────────────────────────────┘
               │
     ┌─────────┼─────────┬──────────┐
     │         │         │          │
     ▼         ▼         ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌───────────┐
│Transport││Accommo- ││  Food   ││Sightseein │
│ Agent   ││ dation  ││  Agent  ││   g      │
│(航班天气)││(酒店民宿)││(餐厅小吃)││(景点门票)│
└─────────┘└─────────┘└─────────┘└───────────┘
```

- **Supervisor**: 主路由 Agent，负责决策下一步调用哪个 Sub-Agent
- **TransportAgent**: 交通领域，处理航班、天气查询
- **AccommodationAgent**: 住宿领域，处理酒店、民宿推荐
- **FoodAgent**: 餐饮领域，处理餐厅、小吃推荐
- **SightseeingAgent**: 景点领域，处理景点推荐、门票查询、本地攻略

## Tech Stack

- **LLM**: ModelScope API (Kimi-K2.5)
- **框架**: LangChain + LangGraph
- **RAG**: Chroma + M3E-Base 向量库
- **地图**: 高德地图 POI 搜索
- **测试**: pytest

## Directory Structure

```
├── CLAUDE.md                  # 项目规范文档
├── .gitignore                 # Git忽略配置
├── .env.example               # 环境变量模板
├── requirements.txt            # 项目依赖
├── pyproject.toml             # black 代码格式化配置
├── amap_api_guide.md           # 高德地图 API 使用指南
├── init_db.py                 # RAG 向量库初始化脚本
├── test_rag.py                # RAG 检索测试脚本
├── scripts/                   # 工具脚本
│   ├── format_markdown.py     # Markdown 层级格式化脚本
│   └── evaluate_agent.py      # Agent 评测流水线脚本
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD 自动化测试
├── config/
│   ├── config.yaml            # 全局配置
│   └── tools.md              # 工具Schema定义
├── data_markdown/             # MinerU 解析的 Markdown 文件
├── chroma_db_md/              # Markdown 向量库
├── src/
│   ├── __init__.py
│   ├── main.py                # 主入口
│   ├── agents/               # Multi-Agent 模块
│   │   ├── graph.py          # LangGraph 工作流定义
│   │   ├── state.py          # Agent 状态定义
│   │   ├── supervisor.py     # Supervisor 主路由 Agent
│   │   ├── main_agent.py     # 单 Agent 模式（备用）
│   │   ├── transport_agent.py
│   │   ├── accommodation_agent.py
│   │   ├── food_agent.py
│   │   └── sightseeing_agent.py
│   ├── skills/               # 工具模块 (LangChain Tools)
│   │   ├── weather_skill.py      # 天气查询
│   │   ├── flight_skill.py       # 航班查询
│   │   ├── scenic_skill.py      # 景点门票
│   │   ├── recommend_skill.py    # 景点推荐
│   │   ├── accommodation_skill.py # 住宿推荐
│   │   ├── food_skill.py        # 美食推荐
│   │   └── local_guide_skill.py # 本地攻略(RAG)
│   ├── prompts/               # Prompt模板管理
│   └── utils/
│       ├── logger.py        # 日志收集器
│       ├── rag_manager.py    # RAG 向量库管理
│       └── amap_service.py   # 高德地图服务
└── tests/
    ├── unit/                  # 单元测试
    └── integration/            # 集成测试
```

## Commands

### 安装依赖
```bash
pip install -r requirements.txt
```

### RAG 向量库初始化
```bash
python scripts/format_markdown.py
python init_db.py
python test_rag.py
```

### 运行主程序
```bash
python src/main.py
```

### 运行单元测试
```bash
pytest tests/unit/ -v
```

### 运行 Agent 评测
```bash
python scripts/evaluate_agent.py
```

---

## Error Handling (Rate Limit & Fallback)

### 限流重试策略

当遇到 API 限流（HTTP 429 或 `choices=null` 畸形响应）时，使用指数退避：

```python
EXPONENTIAL_BACKOFF_DELAYS = [5, 15, 30]  # 第1次5s，第2次15s，第3次30s
```

### choices=null 根因判断

免费 API 限流时常返回畸形响应（`choices: null`），已实现识别：
- 检测 `response.choices` 为空/None
- 检测错误信息包含 `null value for 'choices'`
- 统一归类为 `RateLimitError`，走限流重试逻辑

### Supervisor 失败处理

Supervisor 异常时不立即 FINISH，使用硬编码默认路由顺序：
```python
DEFAULT_ROUTING_ORDER = [
    "TransportAgent",
    "AccommodationAgent", 
    "FoodAgent",
    "SightseeingAgent",
]
```

---

## Coding Conventions (For Claude)

When generating or modifying code in this repository, you MUST adhere to the following rules:

1. **Type Hinting**: All Python functions and methods MUST include strict type hints.

2. **Pydantic Validation**: Use `pydantic` v2 for defining all Agent inputs and Tool schemas.

3. **Docstrings**: Use Google-style docstrings for all classes and functions.

4. **Logging**: Never use `print()`. Always use: `from src.utils.logger import logger`.

5. **Error Handling**: Network calls MUST include try-except and return structured fallback.

6. **Code Formatting**: Use `black src/ tests/ before committing.

7. **Observability**: Every Agent interaction MUST be traced with langchain.callbacks.

8. **Security**: No PII should be sent to LLM.

9. **Testing Thresholds**: New Tools MUST reach >80% code coverage.

10. **Schema Evolution**: Tool schemas MUST remain backward compatible.

---

## Skills (LangChain Tools)

| 工具 | 功能 |
|------|------|
| `weather_query` | 天气查询（7天预报） |
| `flight_search` | 航班查询 |
| `scenic_ticket` | 景点门票查询 |
| `recommend_scenic` | 景点推荐（按场景类型） |
| `search_local_guide` | 本地攻略（RAG检索） |
| `recommend_hotel` | 酒店推荐 |
| `recommend_bnb` | 民宿推荐 |
| `recommend_restaurant` | 餐厅推荐 |
| `recommend_snacks` | 小吃推荐 |

---

## RAG 本地知识库

### 技术栈
- **文本切分**: `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter`
- **向量存储**: Chroma (`./chroma_db_md`)
- **Embedding**: M3E-Base
- **数据源**: `data_markdown/guide_structured.md`

### 使用方式
```python
from src.utils.rag_manager import RAGManager
rag = RAGManager(markdown_path="data_markdown/guide_structured.md")
result = rag.query("去哈尔滨旅游的最佳时间？")
```

---

## 已实现功能

**���通**:
- `flight_search` - 航班查询
- `weather_query` - 天气查询

**景点**:
- `recommend_scenic` - 景点推荐（按场景类型）
- `scenic_ticket` - 门票查询
- `search_local_guide` - 本地攻略（RAG）

**住宿**:
- `recommend_hotel` - 酒店推荐
- `recommend_bnb` - 民宿推荐

**美食**:
- `recommend_restaurant` - 餐厅推荐
- `recommend_snacks` - 小吃推荐

---

## 架构演进

| 阶段 | 状态 |
|------|------|
| LangChain Tool | ✅ 已完成 |
| Multi-Agent (LangGraph) | ✅ 已完成 |
| RAG 知识库 | ✅ 已完成 |
| 高德地图 POI | ✅ 已完成 |
| 真实航班 API | 待接入 |
| 真实门票 API | 待接入 |
| 缓存机制 | 待优化 |