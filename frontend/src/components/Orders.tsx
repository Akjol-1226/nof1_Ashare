import { useState, useEffect } from 'react'
import { tradingWebSocket } from '../services/websocket'
import { apiService } from '../services/api'
import { Order as OrderType } from '../types'

interface DisplayOrder {
  ai_name: string
  side: string
  symbol: string
  quantity: number
  price: number
  status: string
}

export default function Orders() {
  const [orders, setOrders] = useState<DisplayOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // 1. Fetch initial data
    const fetchOrders = async () => {
      try {
        setLoading(true)
        const data = await apiService.getAllOrders()
        const formattedOrders: DisplayOrder[] = data.map((order: OrderType) => ({
          ai_name: order.ai_name,
          side: order.direction.toUpperCase(),
          symbol: order.stock_name || order.stock_code,
          quantity: order.quantity,
          price: order.price,
          status: order.status.charAt(0).toUpperCase() + order.status.slice(1)
        }))
        setOrders(formattedOrders)
      } catch (err) {
        console.error('Failed to fetch orders:', err)
        setError('无法加载订单数据')
      } finally {
        setLoading(false)
      }
    }

    fetchOrders()

    // 2. Connect to WebSocket
    tradingWebSocket.connect()

    // Listen for updates
    const handleMessage = (message: any) => {
      if (message.type === 'trading_update') {
        const data = message.data
        if (data && data.orders) {
          const formattedOrders: DisplayOrder[] = data.orders.map((order: OrderType) => ({
            ai_name: order.ai_name,
            side: order.direction.toUpperCase(),
            symbol: order.stock_name || order.stock_code,
            quantity: order.quantity,
            price: order.price,
            status: order.status.charAt(0).toUpperCase() + order.status.slice(1)
          }))
          // Replace or merge? Usually WS sends the "latest view", so replacing is fine if WS sends full list.
          // In main.py, it sends a list of orders.
          // Wait, main.py sends `orders.extend([{...}])` which is a list of recent orders for ALL AIs.
          // If WS sends "recent 10 orders per AI", it's a list.
          // So replacing entire list is probably intended by current design.
          setOrders(formattedOrders)
        }
      }
    }

    tradingWebSocket.onMessage(handleMessage)

    return () => {
      tradingWebSocket.offMessage(handleMessage)
      tradingWebSocket.disconnect()
    }
  }, [])

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

  if (loading) {
    return (
      <div className="p-4 h-full flex justify-center items-center text-gray-500">
        <p>加载中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 h-full flex justify-center items-center text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  if (orders.length === 0) {
    return (
      <div className="p-4 h-full flex justify-center items-center text-gray-500">
        <p>No orders yet...</p>
      </div>
    )
  }

  return (
    <div className="p-4 h-full">
      <div className="space-y-1 h-full overflow-y-auto">
        <div className="grid grid-cols-4 gap-2 text-xs text-gray-700 font-semibold border-b border-gray-300 py-1">
          <span>SIDE/STOCK</span>
          <span>QUANTITY</span>
          <span className="text-right">报价</span>
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
            <div className="text-right text-gray-800">
              {order.price != null ? `¥${order.price.toFixed(2)}` : '市价'}
            </div>
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
