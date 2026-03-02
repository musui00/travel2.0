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
├── CLAUDE.md              # 项目规范文档
├── config/
│   ├── config.yaml        # 配置文件
│   └── tools.md          # 工具Schema定义
├── src/
│   ├── __init__.py
│   ├── main.py            # 主入口
│   ├── agents/            # 智能体模块
│   │   ├── main_agent.py
│   │   ├── transport_agent.py
│   │   ├── accommodation_agent.py
│   │   ├── sightseeing_agent.py
│   │   └── food_agent.py
│   └── skills/            # 技能工具模块
│       ├── base_skill.py
│       ├── weather_skill.py
│       ├── flight_skill.py
│       └── scenic_skill.py
└── tests/
    └── test_agents.py
```

## Commands

### 运行主程序
```bash
python src/main.py
```

### 运行测试
```bash
pytest tests/
```

### 安装依赖
```bash
pip install openai pyyaml pytest
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
