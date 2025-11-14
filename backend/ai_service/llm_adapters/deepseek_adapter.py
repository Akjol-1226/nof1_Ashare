"""
DeepSeek API适配器
"""

import httpx
from typing import Dict
import logging

from .base_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class DeepSeekAdapter(LLMAdapter):
    """DeepSeek API适配器（兼容OpenAI格式）"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat"
    ):
        """
        初始化
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    async def get_decision(
        self,
        prompt: str,
        portfolio: Dict,
        market_data: Dict
    ) -> str:
        """获取DeepSeek的交易决策"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的A股交易AI，擅长分析市场并做出理性的交易决策。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result['choices'][0]['message']['content']
        
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return '{"action": "hold", "reasoning": "API error"}'


