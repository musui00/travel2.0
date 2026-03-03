"""
日志收集器
统一管理项目日志
"""

import os
import logging
from datetime import datetime
from typing import Optional


class Logger:
    """日志收集器"""

    _instance: Optional["Logger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """设置日志收集器"""
        # 创建logs目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 创建logger
        self._logger = logging.getLogger("travel_planner")
        self._logger.setLevel(logging.DEBUG)

        # 文件handler
        log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加handler
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def debug(self, message: str):
        """调试日志"""
        self._logger.debug(message)

    def info(self, message: str):
        """信息日志"""
        self._logger.info(message)

    def warning(self, message: str):
        """警告日志"""
        self._logger.warning(message)

    def error(self, message: str):
        """错误日志"""
        self._logger.error(message)

    def critical(self, message: str):
        """严重错误日志"""
        self._logger.critical(message)


# 全局logger实例
logger = Logger()
