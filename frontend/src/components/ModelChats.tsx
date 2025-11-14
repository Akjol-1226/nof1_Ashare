import { useState, useEffect } from 'react'

// 模拟数据 - 后续会从WebSocket获取
const mockChats = [
  {
    ai_name: 'Qwen3-Max',
    timestamp: '2025-11-14 11:25',
    reasoning: '基于中兴通讯的技术面分析和市场趋势，股价处于相对低位，有反弹机会。决定买入100股。'
  },
  {
    ai_name: 'Kimi K2',
    timestamp: '2025-11-14 11:20',
    reasoning: '宁德时代近期调整较大，但新能源汽车板块仍有增长潜力。当前价位适合建仓。'
  },
  {
    ai_name: 'DeepSeek V3.1',
    timestamp: '2025-11-14 11:15',
    reasoning: '三安光电作为LED龙头，业绩稳定。考虑在回调时买入，长期看好。'
  }
]

export default function ModelChats() {
  const [chats, setChats] = useState(mockChats)

  // 模拟实时更新 - 后续替换为WebSocket
  useEffect(() => {
    const interval = setInterval(() => {
      // 这里会添加WebSocket监听
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="border-2 border-border flex-grow flex flex-col min-h-[200px] lg:min-h-0">
      <div className="flex justify-between items-center p-4 border-b-2 border-border">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          MODEL_CHATS
        </h2>
      </div>
      <div className="space-y-3 p-4 overflow-y-auto flex-grow">
        {chats.map((chat, index) => (
          <div key={index} className="flex gap-2">
            <div className="w-6 h-6 bg-gray-400 rounded-full flex items-center justify-center text-[10px] font-medium text-white">
              {chat.ai_name.charAt(0)}
            </div>
            <div className="text-xs flex-1">
              <p className="font-semibold">
                {chat.ai_name}{' '}
                <span className="text-gray-700 font-normal ml-2">
                  [{chat.timestamp}]
                </span>
              </p>
              <p className="text-gray-800 mt-1">{chat.reasoning}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
