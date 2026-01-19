"""
AI决策解析器
解析LLM返回的JSON决策
"""

import json
import re
import logging
from typing import Dict, List, Optional

# 导入股票配置
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stock_config import TRADING_STOCKS

logger = logging.getLogger(__name__)


class DecisionParser:
    """AI决策解析器"""
    
    def parse(self, llm_response: str) -> Dict:
        """
        解析LLM响应
        
        Args:
            llm_response: LLM的原始响应文本
            
        Returns:
            {
                "success": True/False,
                "reasoning": "决策理由",
                "actions": [
                    {
                        "action": "buy",
                        "stock_code": "000063",
                        "quantity": 100,
                        "price_type": "market",
                        "reason": "..."
                    }
                ],
                "error": "错误信息（如果有）"
            }
        """
        try:
            # 1. 清理响应（移除markdown标记）
            cleaned = self._clean_response(llm_response)
            
            # 2. 解析JSON
            decision = json.loads(cleaned)
            
            # 3. 验证格式
            self._validate_decision(decision)
            
            # 4. 规范化数据
            normalized = self._normalize_decision(decision)
            
            return {
                "success": True,
                "reasoning": normalized["reasoning"],
                "actions": normalized["actions"],
                "error": None
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            logger.error(f"DecisionParser: {error_msg}\nResponse: {llm_response[:200]}")
            return {
                "success": False,
                "reasoning": "",
                "actions": [],
                "error": error_msg
            }
        except ValueError as e:
            error_msg = f"格式验证失败: {str(e)}"
            logger.error(f"DecisionParser: {error_msg}")
            return {
                "success": False,
                "reasoning": "",
                "actions": [],
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(f"DecisionParser: {error_msg}")
            return {
                "success": False,
                "reasoning": "",
                "actions": [],
                "error": error_msg
            }
    
    def _clean_response(self, response: str) -> str:
        """
        清理LLM响应
        移除markdown代码块标记、多余的空白等
        """
        # 移除markdown代码块标记
        response = re.sub(r'```json\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*', '', response)
        
        # 移除首尾空白
        response = response.strip()
        
        # 尝试提取第一个完整的JSON对象（如果有多余文本）
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        return response
    
    def _validate_decision(self, decision: Dict):
        """
        验证决策格式
        
        Raises:
            ValueError: 如果格式不正确
        """
        # 必须包含reasoning和actions
        if "reasoning" not in decision:
            raise ValueError("缺少reasoning字段")
        if "actions" not in decision:
            raise ValueError("缺少actions字段")
        
        # actions必须是列表
        if not isinstance(decision["actions"], list):
            raise ValueError("actions必须是数组")
        
        # 验证每个action
        for i, action in enumerate(decision["actions"]):
            try:
                self._validate_action(action)
            except ValueError as e:
                raise ValueError(f"actions[{i}]错误: {str(e)}")
    
    def _validate_action(self, action: Dict):
        """
        验证单个操作
        
        Raises:
            ValueError: 如果操作不合法
        """
        # 必需字段
        required = ["action", "stock_code", "quantity"]
        for field in required:
            if field not in action:
                raise ValueError(f"缺少{field}字段")
        
        # 验证action类型
        if action["action"] not in ["buy", "sell"]:
            raise ValueError(f"action必须是buy或sell，当前值: {action['action']}")
        
        # 验证股票代码
        stock_code = action["stock_code"]
        if stock_code not in TRADING_STOCKS:
            raise ValueError(f"股票代码不在交易范围: {stock_code}。可交易股票: {list(TRADING_STOCKS.keys())}")
        
        # 验证数量
        qty = action["quantity"]
        if not isinstance(qty, (int, float)):
            raise ValueError(f"数量必须是数字: {qty}")
        
        qty = int(qty)
        if qty <= 0:
            raise ValueError(f"数量必须是正数: {qty}")
        if qty % 100 != 0:
            raise ValueError(f"数量必须是100的整数倍: {qty}")
    
    def _normalize_decision(self, decision: Dict) -> Dict:
        """
        规范化决策数据
        补充默认值、标准化格式
        """
        # 规范化reasoning
        reasoning = decision.get("reasoning", "").strip()
        if len(reasoning) > 200:
            reasoning = reasoning[:200] + "..."
        
        # 规范化actions
        normalized_actions = []
        for action in decision["actions"]:
            normalized_action = {
                "action": action["action"].lower(),
                "stock_code": action["stock_code"],
                "quantity": int(action["quantity"]),
                "price_type": action.get("price_type", "market").lower(),
                "price": action.get("price"),
                "reason": action.get("reason", "").strip()
            }
            normalized_actions.append(normalized_action)
        
        return {
            "reasoning": reasoning,
            "actions": normalized_actions
        }
    
    def get_action_summary(self, actions: List[Dict]) -> str:
        """
        获取操作摘要（用于日志）
        
        Returns:
            "买入000063 100股, 卖出300750 200股"
        """
        if not actions:
            return "不操作"
        
        summary_parts = []
        for action in actions:
            action_cn = "买入" if action["action"] == "buy" else "卖出"
            summary_parts.append(
                f"{action_cn}{action['stock_code']} {action['quantity']}股"
            )
        
        return ", ".join(summary_parts)

