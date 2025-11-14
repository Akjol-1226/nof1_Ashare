"""
LLM适配器基类
定义统一的接口规范
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMAdapter(ABC):
    """LLM适配器基类"""

    def __init__(self, api_key: str, base_url: str, model_name: str):
        """
        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = None

    @abstractmethod
    def initialize_client(self):
        """初始化客户端"""
        pass

    @abstractmethod
    def call_api(self, messages: List[Dict], temperature: float = 0.7, timeout: int = 30) -> Dict:
        """
        调用LLM API

        Args:
            messages: 消息列表
            temperature: 温度参数
            timeout: 超时时间（秒）

        Returns:
            {
                "success": True/False,
                "response": "LLM响应内容",
                "raw_response": "原始响应",
                "latency_ms": 响应延迟（毫秒）,
                "tokens_used": 使用的token数（如果有）,
                "error": "错误信息"
            }
        """
        pass

    def validate_api_key(self) -> bool:
        """验证API Key是否有效"""
        try:
            # 发送一个简单的测试请求
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            result = self.call_api(test_messages, timeout=10)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"API Key验证失败: {str(e)}")
            return False