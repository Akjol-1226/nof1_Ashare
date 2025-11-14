import { useState, useEffect } from 'react'

// 模拟数据 - 后续会从WebSocket获取
const mockPortfolios = [
  {
    ai_id: 1,
    ai_name: 'Qwen3-Max',
    avatar: 'Q',
    handle: '@qwen3_max',
    total_assets: 101200.50,
    today_pnl: 1200.50,
    positions: [
      { symbol: '000063', cost: 4024.00, pnl_percent: 2.45 },
      { symbol: '300750', cost: 15000.00, pnl_percent: -1.23 }
    ]
  },
  {
    ai_id: 2,
    ai_name: 'Kimi K2',
    avatar: 'K',
    handle: '@kimi_k2',
    total_assets: 98500.25,
    today_pnl: -499.75,
    positions: [
      { symbol: '600703', cost: 8500.00, pnl_percent: -3.21 },
      { symbol: '002594', cost: 12500.00, pnl_percent: 1.89 }
    ]
  },
  {
    ai_id: 3,
    ai_name: 'DeepSeek V3.1',
    avatar: 'D',
    handle: '@deepseek_v31',
    total_assets: 102800.75,
    today_pnl: 2800.75,
    positions: [
      { symbol: '688256', cost: 22000.00, pnl_percent: 4.56 },
      { symbol: '600276', cost: 18000.00, pnl_percent: 2.34 }
    ]
  }
]

export default function Portfolio() {
  const [portfolios, setPortfolios] = useState(mockPortfolios)
  const [currentIndex, setCurrentIndex] = useState(0)

  // 轮播逻辑
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % portfolios.length)
    }, 5000)

    return () => clearInterval(interval)
  }, [portfolios.length])

  const currentPortfolio = portfolios[currentIndex]

  return (
    <div className="p-4 flex flex-col gap-4 h-full">
      {/* AI 信息头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center text-sm font-medium text-white">
            {currentPortfolio.avatar}
          </div>
          <div>
            <p className="font-semibold text-sm">{currentPortfolio.ai_name}</p>
            <p className="text-[10px] text-gray-700">{currentPortfolio.handle}</p>
          </div>
        </div>
        <button className="text-gray-700">
          <span className="material-symbols-outlined">more_horiz</span>
        </button>
      </div>

      {/* 资产统计 */}
      <div className="border border-gray-300 p-2 flex justify-between items-center">
        <div>
          <p className="text-[10px] uppercase text-gray-700">Total Assets</p>
          <p className="text-lg font-bold">
            ¥{currentPortfolio.total_assets.toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] uppercase text-gray-700">Today's P&L</p>
          <p className={`text-sm font-semibold ${
            currentPortfolio.today_pnl >= 0 ? 'text-green-600' : 'text-red-500'
          }`}>
            {currentPortfolio.today_pnl >= 0 ? '+' : ''}
            ¥{Math.abs(currentPortfolio.today_pnl).toLocaleString()}
          </p>
        </div>
      </div>

      {/* 持仓列表 */}
      <div className="space-y-1 flex-grow overflow-y-auto">
        <div className="grid grid-cols-3 gap-2 text-xs text-gray-700 font-semibold border-b border-gray-300 py-1">
          <span>SYMBOL</span>
          <span className="text-right">COST</span>
          <span className="text-right">P&L</span>
        </div>
        {currentPortfolio.positions.map((position, index) => (
          <div key={index} className="grid grid-cols-3 gap-2 items-center text-sm py-0.5">
            <span className="font-bold">{position.symbol}</span>
            <span className="text-right text-xs text-gray-800">
              ¥{position.cost.toLocaleString()}
            </span>
            <span className={`text-right font-semibold ${
              position.pnl_percent >= 0 ? 'text-green-600' : 'text-red-500'
            }`}>
              {position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>

      {/* 轮播指示器 */}
      <div className="flex justify-center gap-2 mt-4">
        {portfolios.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={`w-2 h-2 rounded-full ${
              index === currentIndex ? 'bg-black' : 'bg-gray-300'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
