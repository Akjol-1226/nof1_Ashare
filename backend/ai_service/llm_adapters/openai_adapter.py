"""
OpenAI兼容API适配器
支持所有使用OpenAI格式的LLM服务
"""

import logging
from typing import Dict, List
from openai import OpenAI
from datetime import datetime

from .base_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMAdapter):
    """OpenAI兼容API适配器"""

    def initialize_client(self):
        """初始化OpenAI客户端"""
        if not self.api_key:
            raise ValueError("API Key不能为空")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def call_api(self, messages: List[Dict], temperature: float = 0.7, timeout: int = 30) -> Dict:
        """
        调用OpenAI兼容API

        Args:
            messages: 消息列表
            temperature: 温度参数
            timeout: 超时时间（秒）

        Returns:
            标准响应格式
        """
        if not self.client:
            self.initialize_client()

        start_time = datetime.now()

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                timeout=timeout
            )

            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            content = response.choices[0].message.content

            # 尝试获取token使用情况（有些API不支持）
            tokens_used = None
            try:
                tokens_used = response.usage.total_tokens
            except:
                pass

            return {
                "success": True,
                "response": content,
                "raw_response": response,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "error": None
            }

        except Exception as e:
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            error_msg = str(e)
            logger.error(f"OpenAI API调用失败: {error_msg}")

            return {
                "success": False,
                "response": None,
                "raw_response": None,
                "latency_ms": latency_ms,
                "tokens_used": None,
                "error": error_msg
            }