"""
Prompt构建器
构建发送给LLM的完整提示词
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from models.models import AI, Position
from data_service.akshare_client import Quote


class PromptBuilder:
    """Prompt构建器"""
    
    def build_user_prompt(
        self,
        ai: AI,
        quotes: List[Quote],
        positions: List[Position],
        historical_klines: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> str:
        """
        构建用户提示词（动态数据）
        
        Args:
            ai: AI对象
            quotes: 实时行情列表
            positions: 持仓列表
            historical_klines: 历史K线数据，格式: {stock_code: [kline_data, ...], ...}
            
        Returns:
            完整的用户提示词
        """
        # 实时计算总收益和收益率（避免使用可能过时的数据库字段）
        total_profit = ai.total_assets - ai.initial_cash
        profit_rate = (total_profit / ai.initial_cash * 100) if ai.initial_cash > 0 else 0.0
        
        prompt = f"""【当前时间】
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【市场行情】
{self._format_market_data(quotes)}

【近5日K线数据】
{self._format_historical_klines(historical_klines) if historical_klines else "暂无历史数据"}

【你的账户】
现金: ¥{ai.current_cash:,.2f}
总资产: ¥{ai.total_assets:,.2f}
总收益: ¥{total_profit:,.2f} ({profit_rate:+.2f}%)

【你的持仓】
{self._format_positions(positions, quotes)}

请基于以上信息做出你的交易决策。记住：只输出JSON，不要任何markdown标记或额外文本。
"""
        return prompt
    
    def _format_market_data(self, quotes: List[Quote]) -> str:
        """
        格式化市场数据
        """
        if not quotes:
            return "暂无行情数据"
        
        lines = []
        lines.append("股票代码 | 名称     | 最新价  | 涨跌幅   | 成交量(万手) | 涨停价  | 跌停价")
        lines.append("-" * 80)
        
        for q in quotes:
            # 计算涨跌停价（简化计算，实际应该考虑ST等特殊情况）
            limit_up = q.close_yesterday * 1.10
            limit_down = q.close_yesterday * 0.90
            
            lines.append(
                f"{q.code}   | {q.name:<8} | ¥{q.price:>6.2f} | "
                f"{q.change_percent:>+6.2f}% | {q.volume/10000:>10,.0f} | "
                f"¥{limit_up:>6.2f} | ¥{limit_down:>6.2f}"
            )
        
        return "\n".join(lines)
    
    def _format_positions(self, positions: List[Position], quotes: List[Quote]) -> str:
        """
        格式化持仓数据
        """
        if not positions:
            return "暂无持仓"
        
        # 创建股票代码到行情的映射
        quote_map = {q.code: q for q in quotes}
        
        lines = []
        lines.append("股票代码 | 名称     | 数量  | 可卖  | 成本价  | 现价    | 盈亏")
        lines.append("-" * 70)
        
        for p in positions:
            current_quote = quote_map.get(p.stock_code)
            current_price = current_quote.price if current_quote else p.current_price
            
            lines.append(
                f"{p.stock_code}   | {p.stock_name:<8} | {p.quantity:>5} | "
                f"{p.available_quantity:>5} | ¥{p.avg_cost:>6.2f} | "
                f"¥{current_price:>6.2f} | {p.profit_rate:>+6.2f}%"
            )
        lines.append("-" * 70)
        lines.append("注：'可卖'列显示当前可以卖出的数量（T+1规则：今日买入的明日才能卖）。如果'可卖'为0，则无法卖出。")
        
        return "\n".join(lines)
    
    def _format_historical_klines(self, klines_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        格式化历史K线数据
        
        Args:
            klines_data: {stock_code: [kline_data, ...], ...}
            
        Returns:
            格式化的K线数据字符串
        """
        if not klines_data:
            return "暂无历史数据"
        
        lines = []
        for stock_code, klines in klines_data.items():
            if not klines:
                continue
            
            from stock_config import get_stock_name
            stock_name = get_stock_name(stock_code) or stock_code
            
            lines.append(f"\n【{stock_code} {stock_name}】")
            lines.append("日期         | 开盘   | 最高   | 最低   | 收盘   | 涨跌幅  | 成交量(万手)")
            lines.append("-" * 75)
            
            # 只显示最近5条
            recent_klines = klines[-5:] if len(klines) > 5 else klines
            
            for kline in recent_klines:
                # Biying API 返回格式: {"t": 时间, "o": 开盘, "h": 最高, "l": 最低, "c": 收盘, "v": 成交量, "a": 成交额, "pc": 前收盘, "sf": 停牌}
                time_str = str(kline.get('t', ''))[:10]  # 取前10位作为日期
                open_price = kline.get('o', 0)
                high = kline.get('h', 0)
                low = kline.get('l', 0)
                close = kline.get('c', 0)
                pre_close = kline.get('pc', 0)
                volume = kline.get('v', 0) / 10000  # 转换为万手
                
                # 计算涨跌幅
                change_pct = ((close - pre_close) / pre_close * 100) if pre_close > 0 else 0
                
                lines.append(
                    f"{time_str} | ¥{open_price:>5.2f} | ¥{high:>5.2f} | ¥{low:>5.2f} | "
                    f"¥{close:>5.2f} | {change_pct:>+6.2f}% | {volume:>10,.0f}"
                )
        
        return "\n".join(lines)
    
    def build_system_prompt(self) -> str:
        """
        构建系统提示词（从配置动态生成）
        """
        from stock_config import TRADING_STOCKS, get_stock_full_code
        
        # 动态构建股票列表字符串
        stock_list_str = ""
        for code, name in TRADING_STOCKS.items():
            full_code = get_stock_full_code(code)
            market = "沪A" if full_code.endswith(".SH") else "深A"
            if code.startswith("688"): market = "科创板"
            elif code.startswith("300"): market = "创业板"
            
            stock_list_str += f"   - {code} {name} ({market})\n"
        
        # 去掉末尾的换行
        stock_list_str = stock_list_str.rstrip()
        
        # # 获取第一个股票作为示例
        # example_code = list(TRADING_STOCKS.keys())[0] if TRADING_STOCKS else "000001"
        # example_name = list(TRADING_STOCKS.values())[0] if TRADING_STOCKS else "示例股票"
        # example_name_2 = list(TRADING_STOCKS.values())[1] if len(TRADING_STOCKS) > 1 else "另一只股票"

        system_prompt = f"""# Role
你是一位专业的A股量化交易员，正在参与AI交易竞赛。

# Goal
在与其他AI的竞争中，通过精准的买卖决策，获得最高的收益率。

# Rules
1. 初始资金: 请参考【你的账户】中的"现金"余额
2. 可交易股票: 仅限以下{len(TRADING_STOCKS)}只A股
{stock_list_str}

3. 交易限制:
   - T+1: 当日买入的股票次日才能卖出
   - 涨跌停: 不能在涨停价买入或跌停价卖出
   - 最小单位: 100股（1手）
   - 手续费: 0.025%（买卖双向）
   - 印花税: 0.1%（仅卖出）

# 决策要求
1. 每次决策需输出标准JSON格式
2. 可以选择不操作（持仓观望）
3. 需要简要说明决策理由
4. **买入前必须进行资金检查**：
   - 确认你的现金余额是否 >= 所需金额（股价 × 数量）
   - 如果现金不足，则不能买入，必须选择其他操作或观望
   - 示例：买入100股价格100元的股票，需要资金 = 100 × 100 × 1.00025 ≈ ¥10,002.50


# Output Format
严格按照以下JSON格式输出，不要包含任何markdown标记或额外文本：

{{
  "reasoning": "你的决策分析（100字以内，包含对市场走势的判断和操作理由）",
  "actions": [
    {{
      "action": "buy/sell",
      "stock_code": "你要买入/卖出的股票代码",
      "price_type": "market/limit",
      "price": 25.5 (可选，limit单必填),
      "quantity": 100
    }}
  ]
}}

【字段说明】
- reasoning: 总体决策思路
- actions: 操作列表，可以为空数组[]表示不操作（持仓观望）
  - action: "buy" (买入) 或 "sell" (卖出)
  - stock_code: 6位股票代码
  - price_type: "market" (市价马上成交) 或 "limit" (限价挂单)
  - price: 限价单的价格(Float)，如果是market单则忽略
  - quantity: 数量，必须是100的整数倍
"""
        return system_prompt

    def build_full_prompt(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        构建完整的Prompt（System + User）
        
        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词（可选，如果不传则自动构建）
        
        Returns:
            {"system": "...", "user": "..."}
        """
        if system_prompt is None:
            system_prompt = self.build_system_prompt()
            
        return {
            "system": system_prompt,
            "user": user_prompt
        }

