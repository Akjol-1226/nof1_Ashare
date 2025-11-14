import { useState } from 'react'

// 模拟数据 - 后续会从WebSocket获取
const mockOrders = [
  {
    ai_name: 'Qwen3-Max',
    side: 'BUY',
    symbol: '000063',
    quantity: 100,
    price: 40.24,
    status: 'Filled'
  },
  {
    ai_name: 'Kimi K2',
    side: 'SELL',
    symbol: '300750',
    quantity: 50,
    price: 180.50,
    status: 'Filled'
  },
  {
    ai_name: 'DeepSeek V3.1',
    side: 'BUY',
    symbol: '600703',
    quantity: 200,
    price: 12.85,
    status: 'Pending'
  },
  {
    ai_name: 'Qwen3-Max',
    side: 'BUY',
    symbol: '002594',
    quantity: 150,
    price: 210.30,
    status: 'Filled'
  }
]

export default function Orders() {
  const [orders, setOrders] = useState(mockOrders)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Filled':
        return 'bg-green-100 text-green-800'
      case 'Pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'Rejected':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'text-green-600' : 'text-red-500'
  }

  return (
    <div className="p-4 h-full">
      <div className="space-y-1 h-full overflow-y-auto">
        <div className="grid grid-cols-4 gap-2 text-xs text-gray-700 font-semibold border-b border-gray-300 py-1">
          <span>SIDE/SYMBOL</span>
          <span>QUANTITY</span>
          <span className="text-right">PRICE</span>
          <span className="text-right">STATUS</span>
        </div>
        {orders.map((order, index) => (
          <div key={index} className="grid grid-cols-4 gap-2 items-center text-sm py-0.5">
            <div>
              <span className={`font-bold ${getSideColor(order.side)}`}>
                {order.side}
              </span>
              <span className="ml-1">{order.symbol}</span>
              <div className="text-[10px] text-gray-600">{order.ai_name}</div>
            </div>
            <div className="text-gray-800">{order.quantity.toLocaleString()}</div>
            <div className="text-right text-gray-800">¥{order.price.toFixed(2)}</div>
            <div className="text-right text-xs">
              <span className={`px-2 py-0.5 rounded ${getStatusColor(order.status)}`}>
                {order.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
