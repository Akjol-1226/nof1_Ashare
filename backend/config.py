"""
配置管理模块
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    database_url: str = "sqlite:///./nof1_ashare.db"  # 使用SQLite作为简单开始
    redis_url: str = "redis://localhost:6379/0"
    
    # 服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8888
    
    # 交易配置
    initial_cash: float = 100000.0  # 初始资金（元）
    trading_commission_rate: float = 0.00025  # 佣金费率（万2.5）
    stamp_tax_rate: float = 0.001  # 印花税（0.1%，仅卖出）
    transfer_fee_rate: float = 0.00001  # 过户费（万0.1）
    
    # A股规则配置
    min_lot_size: int = 100  # 最小交易单位（1手=100股）
    price_limit_normal: float = 0.10  # 普通股票涨跌停限制（10%）
    price_limit_st: float = 0.05  # ST股票涨跌停限制（5%）
    
    # AI调度配置
    ai_decision_interval: int = 10  # AI决策间隔（秒）
    llm_timeout: int = 5  # LLM API超时时间（秒）
    
    # LLM API配置（从环境变量自动读取）
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"

    claude_api_key: Optional[str] = None

    # DeepSeek
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Qwen (阿里云百炼)
    dashscope_api_key: Optional[str] = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Kimi (月之暗面)
    moonshot_api_key: Optional[str] = None
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    
    # 日志配置
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()
