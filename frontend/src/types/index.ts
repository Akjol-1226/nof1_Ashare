// AI相关类型
export interface AI {
  id: number
  name: string
  model_type: string
  current_cash: number
  total_assets: number
  total_profit: number
  profit_rate: number
}

// 持仓相关类型
export interface Position {
  stock_code: string
  stock_name: string
  quantity: number
  available_quantity: number
  cost_price: number
  avg_cost: number
  current_price: number
  market_value: number
  profit_loss: number
  profit_loss_percent: number
}

// 订单相关类型
export interface Order {
  id: number
  ai_id: number
  ai_name: string
  stock_code: string
  stock_name: string
  direction: 'buy' | 'sell'
  quantity: number
  price: number
  status: 'pending' | 'filled' | 'rejected'
  created_at: string
}

// 投资组合类型
export interface Portfolio {
  ai_id: number
  ai_name: string
  cash: number
  total_assets: number
  total_profit: number
  profit_rate: number
  positions: Position[]
}

// 决策日志类型
export interface DecisionLog {
  id: number
  timestamp: string
  reasoning: string
  actions: any[]
  latency_ms: number
  tokens_used: number
  error?: string
}

// WebSocket消息类型
export interface WSMessage {
  type: string
  data: any
}

// 市场数据类型
export interface Quote {
  code: string
  name: string
  price: number
  change_percent: number
  volume: number
}