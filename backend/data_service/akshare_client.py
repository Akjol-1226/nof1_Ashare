"""
AKShare数据接口封装
提供缓存、重试和错误处理机制
"""

# 首先导入代理禁用模块
import sys
import os

# 将项目根目录添加到 sys.path（backend 的父目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 将backend目录添加到 sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    import disable_proxy  # 强制禁用代理
except:
    pass

import akshare as ak
import pandas as pd
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import time

from stock_config import TRADING_STOCKS, is_tradable_stock, get_stock_name
from config import settings

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

    def _get_session(self):
        """获取Session"""
        session = requests.Session()
        # 恢复使用系统代理，看看是否能解决连接问题
        return session
    
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
        获取实时行情数据（优先使用 Biying，失败则回退到 AKShare）
        
        Args:
            stock_codes: 股票代码列表，为None则获取所有可交易股票
            
        Returns:
            行情数据列表
        """
        # 如果未指定股票代码，使用配置中的可交易股票列表
        if stock_codes is None:
            stock_codes = list(TRADING_STOCKS.keys())
        else:
            # 标准化股票代码（去掉市场后缀）
            stock_codes = [code.split('.')[0] for code in stock_codes]
        
        cache_key = f"realtime_quotes_{','.join(stock_codes)}"
        
        # 检查缓存
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        logger.info(f"Fetching realtime quotes for {len(stock_codes)} tradable stocks...")

        # 优先使用 Biying 接口
        if settings.biying_license:
            try:
                logger.info("使用 Biying 接口获取实时行情")
                quotes = self._get_realtime_quotes_biying(stock_codes)
                if quotes:
                    self._set_cache(cache_key, quotes)
                    return quotes
                logger.warning("Biying 接口返回空数据，回退到 AKShare")
            except Exception as e:
                error_msg = f"⚠️ Biying 接口失败: {str(e)}"
                print(f"\n{error_msg}")
                print("🔄 正在回退到 AKShare 接口...\n")
                logger.warning(f"{error_msg}，回退到 AKShare")
        
        # 回退到 AKShare
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
    
    def _get_realtime_quotes_biying(self, stock_codes: List[str]) -> List[Quote]:
        """
        使用 Biying 多股实时接口获取行情
        API: /hsrl/ssjy_more/{licence}?stock_codes=000001,000002,...
        返回格式: [{'p': 最新价, 'o': 开盘, 'h': 最高, 'l': 最低, 'yc': 昨收, ...}]
        """
        # 限制最多20支股票
        stock_codes = [code.split(".")[0] for code in stock_codes][:20]
        
        try:
            base = settings.biying_base_url.rstrip("/")
            codes_str = ",".join(stock_codes)
            url = f"{base}/hsrl/ssjy_more/{settings.biying_license}?stock_codes={codes_str}"
            
            logger.info(f"Calling Biying API: {url}")
            print(f"📡 请求 Biying 接口: {url}")
            print(f"🔑 使用 License: {settings.biying_license[:8]}...")
            # 禁用SSL验证以解决连接问题
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # 使用绕过代理的Session
            with self._get_session() as session:
                resp = session.get(url, timeout=5, verify=False)
                resp.raise_for_status()
            
            data = resp.json()
            if not isinstance(data, list):
                logger.error(f"Biying API 返回非列表数据: {data}")
                return []
            
            quotes = []
            for item in data:
                code = str(item.get("dm") or "")
                if not code:
                    continue
                
                code_simple = code.split(".")[0]
                quote_data = {
                    "代码": code_simple,
                    "名称": get_stock_name(code_simple) or TRADING_STOCKS.get(code_simple, code_simple),
                    "最新价": item.get("p", 0),
                    "今开": item.get("o", 0),
                    "最高": item.get("h", 0),
                    "最低": item.get("l", 0),
                    "昨收": item.get("yc", 0),
                    "涨跌幅": item.get("pc", 0),
                    "涨跌额": item.get("ud", 0),
                    "成交量": item.get("v", 0),
                    "成交额": item.get("cje", 0),
                }
                quotes.append(Quote(quote_data))
            
            logger.info(f"Biying 返回 {len(quotes)} 只股票行情")
            return quotes
            
        except Exception as e:
            logger.error(f"Biying API 调用失败: {e}")
            raise
    
    def get_order_book(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取单个股票的买卖五档盘口（来自 Biying 接口）
        API: /hsstock/real/five/{stock_code}/{licence}
        返回格式: {'ps': [卖5到卖1], 'pb': [买1到买5], 'vs': [卖量], 'vb': [买量], 't': 时间}
        """
        if not settings.biying_license:
            logger.warning("未配置 Biying license，无法获取五档盘口")
            return None
        
        cache_key = f"order_book_{stock_code}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            stock_code = stock_code.split(".")[0]  # 去掉市场后缀
            base = settings.biying_base_url.rstrip("/")
            url = f"{base}/hsstock/real/five/{stock_code}/{settings.biying_license}"
            
            logger.info(f"Calling Biying order book API: {url}")
            with self._get_session() as session:
                resp = session.get(url, timeout=3, verify=False)
                resp.raise_for_status()
            
            data = resp.json()
            
            # 转换为标准格式
            order_book = {
                "ask_prices": data.get("ps") or [],    # 卖五到卖一
                "bid_prices": data.get("pb") or [],    # 买一到买五
                "ask_volumes": data.get("vs") or [],   # 卖盘量
                "bid_volumes": data.get("vb") or [],   # 买盘量
                "timestamp": data.get("t"),
            }
            
            self._set_cache(cache_key, order_book)
            logger.info(f"成功获取 {stock_code} 五档盘口")
            return order_book
            
        except Exception as e:
            logger.error(f"获取五档盘口失败 ({stock_code}): {e}")
            return None

    def get_historical_klines(
        self,
        stock_code: str,
        interval: str = "d",
        adjust: str = "n",
        days: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取历史K线数据（使用 Biying API）
        
        Args:
            stock_code: 股票代码（如 000063）
            interval: 分时级别 (5/15/30/60/d/w/m/y)
            adjust: 除权方式 (n不复权/f前复权/b后复权/fr等比前复权/br等比后复权)
            days: 获取最近N天的数据
            
        Returns:
            K线数据列表，格式: [{"t": "时间", "o": 开盘, "h": 最高, "l": 最低, "c": 收盘, "v": 成交量, "a": 成交额, "pc": 前收盘, "sf": 停牌}, ...]
        """
        if not settings.biying_license:
            logger.warning("未配置 Biying license，无法获取历史K线数据")
            return None
        
        cache_key = f"klines_{stock_code}_{interval}_{days}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            # 标准化股票代码（添加市场后缀）
            from stock_config import get_stock_full_code
            full_code = get_stock_full_code(stock_code)
            
            # 构造API URL
            base = settings.biying_base_url.rstrip("/")
            url = f"{base}/hsstock/history/{full_code}/{interval}/{adjust}/{settings.biying_license}?lt={days * 2}"
            
            logger.info(f"Calling Biying K线 API: {url}")
            with self._get_session() as session:
                resp = session.get(url, timeout=5, verify=False)
                resp.raise_for_status()
            
            data = resp.json()
            if not isinstance(data, list):
                logger.error(f"Biying K线 API 返回非列表数据: {data}")
                return None
            
            # 只取最近N天的数据（如果数据量过多）
            if interval == 'd':
                # 日线数据，取最后N条
                klines = data[-days:] if len(data) > days else data
            else:
                # 分钟级数据，取最后的相关条数
                klines = data[-min(len(data), 100):]
            
            self._set_cache(cache_key, klines)
            logger.info(f"成功获取 {stock_code} 的 {len(klines)} 条K线数据")
            return klines
            
        except Exception as e:
            logger.error(f"获取历史K线失败 ({stock_code}): {e}")
            return None

    def _get_mock_quotes(self, stock_codes: List[str]) -> List[Quote]:
        """
        生成模拟的行情数据用于测试
        """
        import random
        from datetime import datetime

        quotes = []
        base_prices = {
            '000063': 25.0,   # 中兴通讯
            '300750': 180.0,  # 宁德时代
            '600703': 15.0,   # 三安光电
            '002594': 25.0,   # 比亚迪
            '688256': 35.0,   # 寒武纪
            '600276': 45.0    # 恒瑞医药
        }

        for code in stock_codes:
            base_price = base_prices.get(code, 20.0)

            # 生成略微波动的价格
            price_variation = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + price_variation)

            # 生成其他数据
            yesterday_close = base_price
            change_amount = current_price - yesterday_close
            change_percent = (change_amount / yesterday_close) * 100

            # 创建Quote对象
            quote = Quote({
                '代码': code,
                '名称': TRADING_STOCKS.get(code, code),
                '最新价': round(current_price, 2),
                '今开': round(base_price * random.uniform(0.98, 1.02), 2),
                '最高': round(max(current_price, base_price * random.uniform(1.01, 1.05)), 2),
                '最低': round(min(current_price, base_price * random.uniform(0.95, 0.99)), 2),
                '昨收': round(yesterday_close, 2),
                '涨跌幅': round(change_percent, 2),
                '涨跌额': round(change_amount, 2),
                '成交量': random.randint(100000, 1000000),
                '成交额': round(current_price * random.randint(100000, 1000000), 2),
                'timestamp': datetime.now().isoformat()
            })

            quotes.append(quote)

        logger.info(f"Generated {len(quotes)} mock quotes")
        return quotes


