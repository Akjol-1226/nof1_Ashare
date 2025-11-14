"""
Claude API适配器
"""

import httpx
from typing import Dict
import logging

from .base_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class ClaudeAdapter(LLMAdapter):
    """Claude API适配器"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229"
    ):
        """
        初始化
        
        Args:
            api_key: API密钥
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
    
    async def get_decision(
        self,
        prompt: str,
        portfolio: Dict,
        market_data: Dict
    ) -> str:
        """获取Claude的交易决策"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "system": "你是一个专业的A股交易AI，擅长分析市场并做出理性的交易决策。",
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result['content'][0]['text']
        
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            return '{"action": "hold", "reasoning": "API error"}'


