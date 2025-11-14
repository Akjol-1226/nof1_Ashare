"""
使用stock_bid_ask_em接口的AKShare客户端
"""

import akshare as ak
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class AKShareClientV2:
    """使用单股票查询接口的客户端"""
    
    def __init__(self, stock_codes: List[str]):
        """
        Args:
            stock_codes: 股票代码列表
        """
        self.stock_codes = stock_codes
        
    def get_realtime_quotes(self) -> List[Dict]:
        """获取所有股票的实时行情"""
        quotes = []
        
        for code in self.stock_codes:
            try:
                df = ak.stock_bid_ask_em(symbol=code)
                data = {}
                for _, row in df.iterrows():
                    data[row['item']] = row['value']
                
                # 转换为统一格式
                quote = {
                    'code': code,
                    'price': data.get('最新', 0),
                    'change_percent': data.get('涨幅', 0),
                    'volume': data.get('总手', 0),
                    'amount': data.get('金额', 0),
                    'high': data.get('最高', 0),
                    'low': data.get('最低', 0),
                    'open': data.get('今开', 0),
                    'close_yesterday': data.get('昨收', 0)
                }
                quotes.append(quote)
                
            except Exception as e:
                logger.error(f"Failed to get quote for {code}: {e}")
                
        return quotes
