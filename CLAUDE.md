# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基于 ModelScope API 的智能旅游规划系统，采用 **多智能体 (Multi-Agent) 架构**。

## Architecture

### 多智能体架构

```
┌─────────────────────────────────────┐
│           MainAgent                 │
│         (主Agent - 全局路由)         │
└───────┬───────┬───────┬───────┬────┘
        │       │       │       │
   ┌────▼┐ ┌───▼┐ ┌───▼┐ ┌───▼┐
   │Transport│ │Accommo-│ │Sight-│ │Food │
   │Agent  │ │dation │ │seeing│ │Agent│
   └────┘ └─────┘ └─────┘ └─────┘
        │       │       │       │
   ┌────▼┐ ┌───▼┐ ┌───▼┐ ┌───▼┐
   │Flight│ │Weather│ │Scenic│ │Base │
   │Skill │ │Skill │ │Skill │ │Skill│
   └─────┘ └──────┘ └──────┘ └─────┘
```

- **MainAgent**: 全局路由，意图拆解，并发调度Sub-agent
- **Sub-agent**: 垂直领域专家（交通、住宿、景点、美食）
- **Skill**: 原子化工具（航班查询、天气查询、门票查询）

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
│   │   ├── main_agent.py
│   │   ├── transport_agent.py
│   │   ├── accommodation_agent.py
│   │   ├── sightseeing_agent.py
│   │   └── food_agent.py
│   ├── skills/                # 技能工具模块
│   │   ├── base_skill.py
│   │   ├── weather_skill.py
│   │   ├── flight_skill.py
│   │   └── scenic_skill.py
│   ├── prompts/                # Prompt模板管理
│   │   ├── main_agent_prompt.yaml
│   │   ├── transport_prompt.yaml
│   │   ├── accommodation_prompt.yaml
│   │   ├── sightseeing_prompt.yaml
│   │   └── food_prompt.yaml
│   └── utils/                 # 通用工具
│       └── logger.py          # 日志收集器
└── tests/
    ├── unit/                  # 单元测试
    │   └── test_skills.py
    └── integration/            # 集成测试
        └── test_agent_workflow.py
```

## Commands

### 运行主程序
```bash
python src/main.py
```

### 运行单元测试
```bash
pytest tests/unit/ -v
```

### 运行集成测试
```bash
pytest tests/integration/ -v
```

### 运行所有测试
```bash
pytest tests/ -v
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## Configuration

配置文件位于 [config/config.yaml](config/config.yaml)，包含：
- ModelScope API 配置
- 模型名称
- 外部API占位配置

## Skills

已封装的原子化技能（详细定义见 [config/tools.md](config/tools.md)）：
- `weather_query` - 天气查询
- `flight_search` - 航班查询
- `scenic_ticket` - 景点门票查询

每个Skill都提供 `get_openai_schema()` 方法，返回符合 OpenAI Function Calling 标准的工具定义。

如需接入真实API，修改对应Skill的execute方法。

---

## Coding Conventions (For Claude)

When generating or modifying code in this repository, you MUST adhere to the following rules:

1. **Type Hinting**: All Python functions and methods MUST include strict type hints for arguments and return values.

2. **Pydantic Validation**: Use `pydantic` v2 for defining all Agent inputs, outputs, and Skill schemas. Do not use raw dictionaries for complex data passing.

3. **Docstrings**: Use Google-style docstrings for all classes and functions.

4. **Logging**: Never use `print()`. Always use the custom logger: `from src.utils.logger import logger`. Log API calls at the `INFO` level and errors at the `ERROR` level.

5. **Error Handling**: Network calls inside Skills must include `try-except` blocks and return a structured fallback response rather than throwing raw exceptions that crash the Agent.

## Development Workflows

### Adding a New Skill

When instructed to create a new Skill, follow these exact steps:

1. Create `src/skills/<skill_name>_skill.py` inheriting from `BaseSkill` (in `base_skill.py`).
2. Implement the `execute` method and the `get_openai_schema` method.
3. Register the schema documentation in `config/tools.md`.
4. Create a corresponding unit test in `tests/unit/test_<skill_name>.py`.
5. Run `pytest tests/unit/test_<skill_name>.py` to verify.

### Updating Prompts

Never hardcode prompt strings in Python files. If an Agent's behavior needs tuning, modify the corresponding `.yaml` file in `src/prompts/`.

### Adding a New Agent

When adding a new Sub-agent:

1. Create `src/agents/<agent_name>_agent.py`.
2. Create corresponding prompt template in `src/prompts/<agent_name>_prompt.yaml`.
3. Register in `src/agents/__init__.py` if needed.
4. Add unit tests in `tests/unit/` and integration tests in `tests/integration/`.
