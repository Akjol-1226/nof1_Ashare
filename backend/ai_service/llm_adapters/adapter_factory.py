"""
LLM适配器工厂
根据AI配置创建对应的适配器实例
"""

import os
import logging
from typing import Optional
from .openai_adapter import OpenAIAdapter
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import settings

logger = logging.getLogger(__name__)


class LLMAdapterFactory:
    """LLM适配器工厂"""

    @staticmethod
    def create_adapter(ai_name: str) -> Optional[OpenAIAdapter]:
        """
        根据AI名称创建适配器

        Args:
            ai_name: AI名称（如 'Qwen3-Max', 'Kimi K2'）

        Returns:
            适配器实例或None
        """
        from ais_config import AI_CONFIGS

        # 查找AI配置
        ai_config = None
        for config in AI_CONFIGS:
            if config['name'] == ai_name:
                ai_config = config
                break

        if not ai_config:
            logger.error(f"未找到AI配置: {ai_name}")
            return None

        # 从环境变量获取API Key
        api_key_env = ai_config['api_key_env']
        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.error(f"环境变量 {api_key_env} 未设置")
            return None

        try:
            adapter = OpenAIAdapter(
                api_key=api_key,
                base_url=ai_config['base_url'],
                model_name=ai_config['model_type']
            )
            adapter.initialize_client()

            logger.info(f"创建适配器成功: {ai_name} ({ai_config['model_type']})")
            return adapter

        except Exception as e:
            logger.error(f"创建适配器失败 {ai_name}: {str(e)}")
            return None

    @staticmethod
    def _get_base_url(model_type: str) -> Optional[str]:
        """
        根据模型类型获取base_url

        Args:
            model_type: 模型类型

        Returns:
            base_url或None
        """
        url_mapping = {
            # Qwen系列
            'qwen-plus': settings.dashscope_base_url,
            'qwen-max': settings.dashscope_base_url,
            'qwen-turbo': settings.dashscope_base_url,

            # Kimi系列
            'kimi-k2-turbo-preview': settings.moonshot_base_url,
            'kimi-k1-speed': settings.moonshot_base_url,

            # DeepSeek系列
            'deepseek-chat': settings.deepseek_base_url,
            'deepseek-coder': settings.deepseek_base_url,

            # OpenAI系列（如果需要）
            'gpt-4': settings.openai_base_url,
            'gpt-3.5-turbo': settings.openai_base_url,

            # Claude（如果需要）
            'claude-3-sonnet': 'https://api.anthropic.com/v1',  # 需要单独适配器
        }

        return url_mapping.get(model_type)

    @staticmethod
    def validate_adapter(adapter: OpenAIAdapter) -> bool:
        """
        验证适配器是否可用

        Args:
            adapter: 适配器实例

        Returns:
            是否可用
        """
        if not adapter:
            return False

        try:
            result = adapter.call_api(
                messages=[{"role": "user", "content": "Hello"}],
                timeout=10
            )
            return result.get("success", False)
        except Exception as e:
            logger.error(f"适配器验证失败: {str(e)}")
            return False
