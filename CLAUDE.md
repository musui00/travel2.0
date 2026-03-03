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
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD 自动化测试
├── config/
│   ├── config.yaml            # 全局配置
│   └── tools.md              # 工具Schema定义
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
│       └── logger.py          # 日志收集器
└── tests/
    ├── unit/                  # 单元测试
    └── integration/            # 集成测试
```

## Commands

### 运行主程序
```bash
pip install -r requirements.txt
python src/main.py
```

### 运行单元测试
```bash
pytest tests/unit/ -v
```

---

## Coding Conventions (For Claude)

When generating or modifying code in this repository, you MUST adhere to the following rules:

1. **Type Hinting**: All Python functions and methods MUST include strict type hints for arguments and return values.

2. **Pydantic Validation**: Use `pydantic` v2 for defining all Agent inputs, outputs, and Tool schemas. Do not use raw dictionaries for complex data passing.

3. **Docstrings**: Use Google-style docstrings for all classes and functions.

4. **Logging**: Never use `print()`. Always use the custom logger: `from src.utils.logger import logger`. Log API calls at the `INFO` level and errors at the `ERROR` level.

5. **Error Handling**: Network calls inside Tools must include `try-except` blocks and return a structured fallback response rather than throwing raw exceptions that crash the Agent.

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
