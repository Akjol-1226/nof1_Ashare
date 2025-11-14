"""
AKShare数据接口封装
提供缓存、重试和错误处理机制
"""

# 首先导入代理禁用模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import disable_proxy  # 强制禁用代理
except:
    pass

import akshare as ak
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging
import time

from stock_config import TRADING_STOCKS, is_tradable_stock, get_stock_name

logger = logging.getLogger(__name__)


class Quote:
    """行情数据模型"""
    
    def __init__(self, data: Dict):
        self.code = data.get('代码', '')
        self.name = data.get('名称', '')
        self.price = float(data.get('最新价', 0))
        self.open_price = float(data.get('今开', 0))
        self.high = float(data.get('最高', 0))
        self.low = float(data.get('最低', 0))
        self.close_yesterday = float(data.get('昨收', 0))
        self.change_percent = float(data.get('涨跌幅', 0))
        self.change_amount = float(data.get('涨跌额', 0))
        self.volume = float(data.get('成交量', 0))
        self.amount = float(data.get('成交额', 0))
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'price': self.price,
            'open_price': self.open_price,
            'high': self.high,
            'low': self.low,
            'close_yesterday': self.close_yesterday,
            'change_percent': self.change_percent,
            'change_amount': self.change_amount,
            'volume': self.volume,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat()
        }


class StockInfo:
    """股票基本信息"""
    
    def __init__(self, code: str, name: str):
        self.code = code
        self.name = name
    
    def to_dict(self) -> Dict:
        return {'code': self.code, 'name': self.name}


class AKShareClient:
    """AKShare客户端封装"""
    
    def __init__(self, cache_expire: int = 10, max_retries: int = 3):
        """
        初始化
        
        Args:
            cache_expire: 缓存过期时间（秒）
            max_retries: 最大重试次数
        """
        self.cache_expire = cache_expire
        self.max_retries = max_retries
        self._cache: Dict = {}
        logger.info("AKShareClient initialized")
    
    def _retry_on_error(self, func, *args, **kwargs):
        """
        错误重试装饰器
        """
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(1 * (attempt + 1))  # 递增等待时间
    
    def _get_from_cache(self, key: str) -> Optional[any]:
        """从缓存获取数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self.cache_expire:
                logger.debug(f"Cache hit: {key}")
                return data
        return None
    
    def _set_cache(self, key: str, data: any):
        """设置缓存"""
        self._cache[key] = (data, datetime.now())
    
    def get_realtime_quotes(self, stock_codes: Optional[List[str]] = None) -> List[Quote]:
        """
        获取实时行情数据（仅限可交易股票）
        使用stock_bid_ask_em接口逐个查询，更稳定
        
        Args:
            stock_codes: 股票代码列表，为None则获取所有可交易股票
            
        Returns:
            行情数据列表
        """
        # 如果未指定股票代码，使用配置中的可交易股票列表
        if stock_codes is None:
            stock_codes = list(TRADING_STOCKS.keys())
        else:
            # 过滤出可交易的股票
            stock_codes = [code.split('.')[0] for code in stock_codes if is_tradable_stock(code)]
        
        cache_key = f"realtime_quotes_{','.join(stock_codes)}"
        
        # 检查缓存
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        logger.info(f"Fetching realtime quotes for {len(stock_codes)} tradable stocks...")
        
        quotes = []
        for code in stock_codes:
            try:
                # 使用单股票查询接口（更稳定）
                df = self._retry_on_error(ak.stock_bid_ask_em, symbol=code)
                
                # 解析数据
                data = {}
                for _, row in df.iterrows():
                    data[row['item']] = row['value']
                
                # 转换为Quote对象需要的格式
                quote_data = {
                    '代码': code,
                    '名称': get_stock_name(code) or TRADING_STOCKS.get(code, code),
                    '最新价': data.get('最新', 0),
                    '今开': data.get('今开', 0),
                    '最高': data.get('最高', 0),
                    '最低': data.get('最低', 0),
                    '昨收': data.get('昨收', 0),
                    '涨跌幅': data.get('涨幅', 0),
                    '涨跌额': data.get('涨跌', 0),
                    '成交量': data.get('总手', 0) * 100,  # 转换为股数
                    '成交额': data.get('金额', 0)
                }
                
                quote = Quote(quote_data)
                quotes.append(quote)
                
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {code}: {str(e)}")
                # 继续获取其他股票，不因一只股票失败而全部失败
                continue
        
        if quotes:
            # 缓存结果
            self._set_cache(cache_key, quotes)
            logger.info(f"Successfully fetched {len(quotes)}/{len(stock_codes)} quotes")
        else:
            logger.error("Failed to fetch any quotes")
        
        return quotes
    
    def get_all_stock_list(self) -> List[StockInfo]:
        """
        获取所有A股股票列表
        
        Returns:
            股票信息列表
        """
        cache_key = "all_stock_list"
        
        # 检查缓存（股票列表缓存时间更长）
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < 3600:  # 1小时缓存
                return data
        
        try:
            logger.info("Fetching stock list from AKShare...")
            df = self._retry_on_error(ak.stock_info_a_code_name)
            
            stocks = [StockInfo(row['code'], row['name']) for _, row in df.iterrows()]
            
            # 缓存结果
            self._set_cache(cache_key, stocks)
            
            logger.info(f"Fetched {len(stocks)} stocks")
            return stocks
            
        except Exception as e:
            logger.error(f"Failed to fetch stock list: {str(e)}")
            return []
    
    def get_historical_data(
        self, 
        stock_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取历史行情数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 (daily/weekly/monthly)
            adjust: 复权类型 (qfq前复权/hfq后复权/不复权)
            
        Returns:
            历史数据DataFrame
        """
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            
            logger.info(f"Fetching historical data for {stock_code}")
            df = self._retry_on_error(
                ak.stock_zh_a_hist,
                symbol=stock_code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {stock_code}: {str(e)}")
            return pd.DataFrame()
    
    def get_minute_data(
        self,
        stock_code: str,
        period: str = "5",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取分钟级数据
        
        Args:
            stock_code: 股票代码
            period: 周期 (1/5/15/30/60)
            adjust: 复权类型
            
        Returns:
            分钟数据DataFrame
        """
        try:
            logger.info(f"Fetching minute data for {stock_code}")
            df = self._retry_on_error(
                ak.stock_zh_a_hist_min_em,
                symbol=stock_code,
                period=period,
                adjust=adjust
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch minute data for {stock_code}: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取单个股票的实时信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票信息字典
        """
        quotes = self.get_realtime_quotes([stock_code])
        if quotes:
            return quotes[0].to_dict()
        return None


