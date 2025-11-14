"""
AI配置文件
定义所有参与交易的AI
"""

# AI配置列表
AI_CONFIGS = [
    {
        "name": "Qwen3-Max",
        "model_type": "qwen-plus",
        "api_key_env": "DASHSCOPE_API_KEY",  # 从环境变量读取
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "strategy": "conservative",
        "temperature": 0.5,
        "initial_cash": 100000.0,
    },
    {
        "name": "Kimi K2",
        "model_type": "kimi-k2-turbo-preview",
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "strategy": "balanced",
        "temperature": 0.6,
        "initial_cash": 100000.0,
    },
    {
        "name": "DeepSeek V3.1",
        "model_type": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "strategy": "aggressive",
        "temperature": 0.8,
        "initial_cash": 100000.0,
    },
]

