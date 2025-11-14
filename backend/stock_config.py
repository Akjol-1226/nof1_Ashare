"""
可交易股票配置
限制AI只能交易指定的6只股票
"""

# 可交易股票列表
TRADING_STOCKS = {
    '000063': '中兴通讯',    # 000063.SZ
    '300750': '宁德时代',    # 300750.SZ
    '600703': '三安光电',    # 600703.SH
    '002594': '比亚迪',      # 002594.SZ
    '688256': '寒武纪',      # 688256.SH
    '600276': '恒瑞医药',    # 600276.SH
}

def get_stock_full_code(code: str) -> str:
    """
    获取股票的完整代码（带市场后缀）
    
    Args:
        code: 股票代码（6位数字）
        
    Returns:
        完整代码（如：000063.SZ）
    """
    if code.startswith(('000', '002', '300')):
        return f"{code}.SZ"
    else:
        return f"{code}.SH"

def is_tradable_stock(code: str) -> bool:
    """
    检查股票是否可交易
    
    Args:
        code: 股票代码（6位数字或完整代码）
        
    Returns:
        是否可交易
    """
    # 移除市场后缀（如果有）
    code = code.split('.')[0]
    return code in TRADING_STOCKS

def get_stock_name(code: str) -> str:
    """
    获取股票名称
    
    Args:
        code: 股票代码（6位数字或完整代码）
        
    Returns:
        股票名称，如果不存在返回None
    """
    code = code.split('.')[0]
    return TRADING_STOCKS.get(code)

def get_all_trading_stocks():
    """
    获取所有可交易股票列表
    
    Returns:
        [(code, name, full_code), ...]
    """
    return [
        (code, name, get_stock_full_code(code))
        for code, name in TRADING_STOCKS.items()
    ]

