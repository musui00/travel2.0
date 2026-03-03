"""
Prompt模板管理模块
统一管理所有Agent的提示词配置
"""

import os
import yaml
from typing import Dict, Any


def load_prompt(prompt_file: str) -> Dict[str, str]:
    """
    加载Prompt配置文件

    Args:
        prompt_file: prompt文件名（如 main_agent_prompt.yaml）

    Returns:
        包含所有prompt的字典
    """
    prompts_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(prompts_dir, prompt_file)

    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_main_agent_prompts() -> Dict[str, str]:
    """获取主Agent的prompts"""
    return load_prompt('main_agent_prompt.yaml')


def get_transport_prompts() -> Dict[str, str]:
    """获取交通Agent的prompts"""
    return load_prompt('transport_prompt.yaml')


def get_accommodation_prompts() -> Dict[str, str]:
    """获取住宿Agent的prompts"""
    return load_prompt('accommodation_prompt.yaml')


def get_sightseeing_prompts() -> Dict[str, str]:
    """获取景点Agent的prompts"""
    return load_prompt('sightseeing_prompt.yaml')


def get_food_prompts() -> Dict[str, str]:
    """获取美食Agent的prompts"""
    return load_prompt('food_prompt.yaml')


__all__ = [
    'load_prompt',
    'get_main_agent_prompts',
    'get_transport_prompts',
    'get_accommodation_prompts',
    'get_sightseeing_prompts',
    'get_food_prompts'
]
