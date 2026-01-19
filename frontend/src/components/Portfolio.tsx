import { useState, useEffect } from 'react'
import { tradingWebSocket } from '../services/websocket'
import { apiService } from '../services/api'
import { Portfolio as PortfolioType, Position } from '../types'

interface DisplayPortfolio {
  ai_id: number
  ai_name: string
  avatar: string
  handle: string
  total_assets: number
  total_pnl: number
  positions: {
    stock_code: string
    stock_name: string
    quantity: number
    available: number
    avg_cost: number
    current_price: number
    market_value: number
    profit: number
    profit_percent: number
  }[]
}

export default function Portfolio() {
  const [portfolios, setPortfolios] = useState<DisplayPortfolio[]>([])

  useEffect(() => {
    // 1. Initial Fetch: 主动获取一次数据，避免干等 WebSocket
    const fetchInitialData = async () => {
      try {
        const rankings = await apiService.getAIRanking();
        // 转换 Ranking 数据格式为 DisplayPortfolio
        const formatted = rankings.map((r: any) => ({
          ai_id: r.ai_id,
          ai_name: r.ai_name,
          avatar: r.ai_name.charAt(0).toUpperCase(),
          handle: `@${r.ai_name.toLowerCase().replace(/\s+/g, '_')}`,
          total_assets: r.total_assets,
          total_pnl: r.profit_loss,
          positions: (r.positions || []).map((pos: Position) => ({
            stock_code: pos.stock_code,
            stock_name: pos.stock_name || pos.stock_code,
            quantity: pos.quantity,
            available: pos.available_quantity,
            avg_cost: pos.avg_cost,
            current_price: pos.current_price,
            market_value: pos.market_value,
            profit: pos.profit_loss,
            profit_percent: pos.profit_loss_percent
          }))
        }));
        setPortfolios(formatted);
      } catch (e) {
        console.error("Failed to fetch initial portfolio data:", e);
      }
    };

    fetchInitialData();

    // 2. WebSocket Connection
    tradingWebSocket.connect()

    // Listen for updates
    const handleMessage = (message: any) => {
      if (message.type === 'trading_update') {
        const data = message.data
        if (data && data.portfolios) {
          const formattedPortfolios: DisplayPortfolio[] = data.portfolios.map((p: PortfolioType) => ({
            ai_id: p.ai_id,
            ai_name: p.ai_name,
            avatar: p.ai_name.charAt(0).toUpperCase(),
            handle: `@${p.ai_name.toLowerCase().replace(/\s+/g, '_')}`,
            total_assets: p.total_assets,
            total_pnl: p.total_profit,
            positions: p.positions.map((pos: Position) => ({
              stock_code: pos.stock_code,
              stock_name: pos.stock_name || pos.stock_code,
              quantity: pos.quantity,
              available: pos.available_quantity,
              avg_cost: pos.avg_cost,
              current_price: pos.current_price,
              market_value: pos.market_value,
              profit: pos.profit_loss,
              profit_percent: pos.profit_loss_percent
            }))
          }))
          setPortfolios(formattedPortfolios)
        }
      }
    }

    tradingWebSocket.onMessage(handleMessage)

    return () => {
      tradingWebSocket.offMessage(handleMessage)
      tradingWebSocket.disconnect()
    }
  }, [])

  if (portfolios.length === 0) {
    return (
      <div className="p-4 flex flex-col gap-4 h-full justify-center items-center text-gray-500">
        <p>正在获取市场数据...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {portfolios.map((portfolio, portfolioIndex) => (
        <div key={portfolio.ai_id}>
          <div className="p-4 flex flex-col gap-2">
            {/* AI 信息头部 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center text-sm font-medium text-white">
                  {portfolio.avatar}
                </div>
                <div>
                  <p className="font-semibold text-sm">{portfolio.ai_name}</p>
                  <p className="text-[10px] text-gray-700">{portfolio.handle}</p>
                </div>
              </div>
            </div>

            {/* 总资产概览 */}
            <div className="border border-gray-200 rounded p-2 flex justify-between items-center">
              <div>
                <p className="text-[10px] text-gray-500">总资产</p>
                <p className="text-base font-bold text-gray-800">
                  ¥{portfolio.total_assets.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="text-right">
                <p className="text-[10px] text-gray-500">总盈亏</p>
                <p className={`text-sm font-bold ${portfolio.total_pnl >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {portfolio.total_pnl >= 0 ? '+' : ''}
                  ¥{Math.abs(portfolio.total_pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            {/* 持仓列表 - 券商风格 */}
            <div className="space-y-1">
              {/* 表头 */}
              <div className="grid grid-cols-4 gap-1 text-xs text-gray-400 font-normal py-1 px-1">
                <span>名称/代码</span>
                <span className="text-right">持股/可用</span>
                <span className="text-right">现价/成本</span>
                <span className="text-right">盈亏/比率</span>
              </div>

              {/* 持仓数据行 */}
              {portfolio.positions.map((pos, index) => (
                <div key={index} className="grid grid-cols-4 gap-1 items-center py-2 px-1 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">

                  {/* 列1: 名称 & 代码 */}
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-bold text-gray-800 truncate">{pos.stock_name}</span>
                    <span className="text-xs text-gray-400">{pos.stock_code}</span>
                  </div>

                  {/* 列2: 持股 & 可用 */}
                  <div className="flex flex-col text-right">
                    <span className="text-sm font-medium text-gray-800">{pos.quantity}</span>
                    <span className="text-xs text-gray-400">{pos.available}</span>
                  </div>

                  {/* 列3: 现价 & 成本 */}
                  <div className="flex flex-col text-right">
                    <span className="text-sm font-medium text-gray-800">
                      {pos.current_price.toFixed(2)}
                    </span>
                    <span className="text-xs text-gray-400">{pos.avg_cost.toFixed(2)}</span>
                  </div>

                  {/* 列4: 盈亏额 & 盈亏比 */}
                  <div className="flex flex-col text-right">
                    <span className={`text-sm font-bold ${pos.profit >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {pos.profit >= 0 ? '+' : ''}{Math.round(pos.profit).toLocaleString()}
                    </span>
                    <span className={`text-xs ${pos.profit_percent >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {pos.profit_percent >= 0 ? '+' : ''}{pos.profit_percent.toFixed(2)}%
                    </span>
                  </div>

                </div>
              ))}

              {portfolio.positions.length === 0 && (
                <div className="text-center text-xs text-gray-400 py-6 bg-gray-50 rounded border border-dashed border-gray-200">
                  暂无持仓
                </div>
              )}
            </div>
          </div>

          {/* 模型之间的分割线,最后一个模型不显示 */}
          {portfolioIndex < portfolios.length - 1 && (
            <div className="border-t-2 border-gray-400 my-2 mx-4" />
          )}
        </div>
      ))}
    </div>
  )
}
