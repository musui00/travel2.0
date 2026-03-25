# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基于 ModelScope API 的智能旅游规划系统，采用 **LangChain Agent 架构**。

## Architecture

### LangChain 架构

```
┌─────────────────────────────────────┐
│           MainAgent                 │
│    (LangChain Agent + Tools)        │
└──────────────┬──────────────────────┘
               │
         ┌─────▼─────┐
         │  Tools    │
         ├───────────┤
         │weather_query│
         │flight_search│
         │scenic_ticket │
         └───────────┘
```

- **MainAgent**: LangChain Agent，负责理解用户意图、调用工具、生成规划
- **Tools**: LangChain Tool，原子化工具（天气查询、航班查询、门票查询）

## Tech Stack

- **LLM**: ModelScope API (Kimi-K2.5)
- **框架**: LangChain
- **测试**: pytest

## Directory Structure

```
├── CLAUDE.md                  # 项目规范文档
├── .gitignore                 # Git忽略配置
├── .env.example               # 环境变量模板
├── requirements.txt            # 项目依赖
├── pyproject.toml             # black 代码格式化配置
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
├── data/                      # PDF 源文件（已废弃）
├── data_markdown/             # MinerU 解析的 Markdown 文件
│   ├── 哈尔滨旅游攻略.md       # 原始扁平化标题
│   └── guide_structured.md    # 大模型重构后的多级标题
├── chroma_db/                 # PDF 向量库（已废弃）
├── chroma_db_md/              # Markdown 向量库
├── src/
│   ├── __init__.py
│   ├── main.py                # 主入口
│   ├── agents/                # 智能体模块
│   │   └── main_agent.py     # LangChain Agent
│   ├── skills/                # 工具模块 (LangChain Tools)
│   │   ├── weather_skill.py
│   │   ├── flight_skill.py
│   │   └── scenic_skill.py
│   ├── prompts/                # Prompt模板管理
│   │   └── main_agent_prompt.yaml
│   └── utils/                 # 通用工具
│       ├── logger.py          # 日志收集器
│       └── rag_manager.py     # RAG 向量库管理
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
# 步骤1：使用大模型重构 Markdown 标题层级（扁平化 # → 多级 ##/###）
python scripts/format_markdown.py

# 步骤2：加载重构后的 Markdown 并创建向量库
python init_db.py

# 测试 RAG 检索
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

## Coding Conventions (For Claude)

When generating or modifying code in this repository, you MUST adhere to the following rules:

1. **Type Hinting**: All Python functions and methods MUST include strict type hints for arguments and return values.

2. **Pydantic Validation**: Use `pydantic` v2 for defining all Agent inputs, outputs, and Tool schemas. Do not use raw dictionaries for complex data passing.

3. **Docstrings**: Use Google-style docstrings for all classes and functions.

4. **Logging**: Never use `print()`. Always use the custom logger: `from src.utils.logger import logger`. Log API calls at the `INFO` level and errors at the `ERROR` level.

5. **Error Handling**: Network calls inside Tools must include `try-except` blocks and return a structured fallback response rather than throwing raw exceptions that crash the Agent.

6. **Code Formatting**: Use `black` for code formatting. Run `black src/ tests/` before committing. The project includes `pyproject.toml` configured for black.

## Development Workflows

### Adding a New Tool

When instructed to create a new Tool, follow these exact steps:

1. Create `src/skills/<tool_name>_skill.py` using LangChain `@tool` decorator.
2. Implement the function with proper type hints and docstring.
3. Register the tool in `src/skills/__init__.py`.
4. Update schema documentation in `config/tools.md`.
5. Create a corresponding unit test in `tests/unit/test_<tool_name>.py`.

### Updating Prompts

Never hardcode prompt strings in Python files. If an Agent's behavior needs tuning, modify the corresponding `.yaml` file in `src/prompts/`.

---

## Skills

使用 LangChain `@tool` 装饰器定义的工具：
- `weather_query` - 天气查询
- `flight_search` - 航班查询
- `scenic_ticket` - 景点门票查询

如需接入真实API，修改对应 Tool 函数。

---

## RAG 本地知识库

### 技术栈

- **文本切分**: `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter`
- **向量存储**: Chroma (持久化至 `./chroma_db_md`)
- **Embedding**: M3E-Base (`moka-ai/m3e-base`)
- **数据源**: MinerU 解析的 Markdown 文件 (`data_markdown/`)

### 切分策略

1. **一级切分**: `MarkdownHeaderTextSplitter` 按 `#` `##` `###` 标题层级切分，保留章节 metadata
2. **二级切分**: `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)` 防止单块过长
3. **数据清洗**: 删除 `![](...)` 图片链接，压缩多余换行

### 使用方式

```python
from src.utils.rag_manager import RAGManager

# 初始化（使用重构后的层级化 Markdown）
rag = RAGManager(markdown_path="data_markdown/guide_structured.md")

# 查询（返回内容 + 章节标题层级）
result = rag.query("去哈尔滨旅游的最佳时间是什么时候？")
print(result)
```

---

## Project Requirements

### 待完成事项 (Todo)

- [x] 修复 flight_skill.py 参数名 (departure -> from_city, destination -> to_city)
- [x] 修复 scenic_skill.py 参数名 (city + scenic -> scenic_name)
- [x] 修复 main_agent.py 的 langchain 导入错误
- [x] 更新测试用例参数
- [x] 实现图片场景识别功能
- [x] 实现景点相似度匹配逻辑
- [x] 更新 main.py 交互流程
- [x] 优化交通推荐逻辑（同城/跨城区分）
- [x] 丰富景点推荐内容（详细描述、亮点、活动、贴士）

### 待优化事项

- [ ] 接入真实航班API（航旅纵横/飞常准）
- [ ] 接入真实门票API
- [ ] 增加缓存机制减少API调用
- [ ] 完善单元测试覆盖（新增住宿、餐饮测试）

### 已实现功能

**景点相关**：
- `recommend_scenic` - 景点推荐：根据场景类型推荐相似景点
- `scenic_ticket` - 景点门票查询

**天气交通**：
- `weather_query` - 天气查询（7天预报）
- `flight_search` - 航班查询

**住宿推荐**：
- `recommend_hotel` - 酒店推荐（豪华/舒适/经济）
- `recommend_bnb` - 民宿推荐

**美食推荐**：
- `recommend_restaurant` - 餐厅推荐（按菜系）
- `recommend_snacks` - 小吃推荐

### 架构演进

1. **LangChain Tool** - 原子化工具（当前阶段）
2. **Sub-Agent** - 领域专家Agent（规划中）
   - AccommodationAgent - 住宿领域
   - FoodAgent - 餐饮领域
   - TransportAgent - 交通领域
3. **RAG 知识库** - 本地文档检索（已完成）
   - 支持 Markdown 结构化切分
   - 保留章节层级 metadata
   - 支持向量相似度检索
