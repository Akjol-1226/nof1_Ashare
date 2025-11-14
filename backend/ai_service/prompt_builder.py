"""
Prompt构建器
构建发送给LLM的完整提示词
"""

from typing import List, Dict
from datetime import datetime
from models.models import AI, Position
from data_service.akshare_client import Quote


class PromptBuilder:
    """Prompt构建器"""
    
    def build_user_prompt(
        self,
        ai: AI,
        quotes: List[Quote],
        positions: List[Position]
    ) -> str:
        """
        构建用户提示词（动态数据）
        
        Args:
            ai: AI对象
            quotes: 实时行情列表
            positions: 持仓列表
            
        Returns:
            完整的用户提示词
        """
        prompt = f"""【当前时间】
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【市场行情】
{self._format_market_data(quotes)}

【你的账户】
现金: ¥{ai.current_cash:,.2f}
总资产: ¥{ai.total_assets:,.2f}
总收益: ¥{ai.total_profit:,.2f} ({ai.profit_rate:+.2f}%)

【你的持仓】
{self._format_positions(positions, quotes)}

【历史表现】
交易次数: {ai.trade_count}
胜率: {ai.win_rate:.1f}%

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
        
        return "\n".join(lines)
    
    def build_full_prompt(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, str]:
        """
        构建完整的Prompt（System + User）
        
        Returns:
            {"system": "...", "user": "..."}
        """
        return {
            "system": system_prompt,
            "user": user_prompt
        }

