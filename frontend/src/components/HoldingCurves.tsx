'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { performanceWebSocket } from '../services/websocket'


export default function HoldingCurves() {
  const [performanceData, setPerformanceData] = useState<any[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // 连接 WebSocket
    performanceWebSocket.connect()

    // 监听连接状态
    performanceWebSocket.onOpen(() => {
      setIsConnected(true)
      console.log('✅ Connected to performance WebSocket')
    })

    performanceWebSocket.onClose(() => {
      setIsConnected(false)
      console.log('❌ Disconnected from performance WebSocket')
    })

    // 监听消息
    performanceWebSocket.onMessage((data: any) => {
      if (data.type === 'performance_update') {
        const snapshots = data.data?.snapshots || []
        console.log('📊 Received performance data:', snapshots.length, 'snapshots')
        setPerformanceData(snapshots)
      }
    })

    return () => {
      performanceWebSocket.disconnect()
    }
  }, [])

  // 将性能数据转换为图表需要的格式
  const chartData = performanceData.length > 0 ? (() => {
    // 按时间分组数据
    const timeGrouped: { [key: string]: any } = {}

    performanceData.forEach((snapshot: any) => {
      const timestamp = snapshot.timestamp
      if (!timeGrouped[timestamp]) {
        timeGrouped[timestamp] = { timestamp }
      }

      // 根据AI名称设置对应的资产值（不区分大小写）
      const aiNameLower = (snapshot.ai_name || '').toLowerCase()
      if (aiNameLower.includes('qwen')) {
        timeGrouped[timestamp].qwen = snapshot.total_assets
      } else if (aiNameLower.includes('kimi')) {
        timeGrouped[timestamp].kimi = snapshot.total_assets
      } else if (aiNameLower.includes('deepseek')) {
        timeGrouped[timestamp].deepseek = snapshot.total_assets
      }
    })

    // 转换为数组并按时间排序
    const result = Object.values(timeGrouped).sort((a: any, b: any) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    // 确保每个时间点都有所有AI的数据，如果没有则填充前一个值或默认值
    result.forEach((item: any, index: number) => {
      if (!item.qwen) item.qwen = index > 0 ? (result[index - 1] as any).qwen : 500000
      if (!item.kimi) item.kimi = index > 0 ? (result[index - 1] as any).kimi : 500000
      if (!item.deepseek) item.deepseek = index > 0 ? (result[index - 1] as any).deepseek : 500000
    })

    return result // 显示所有数据点
  })() : [
    // 使用从数据库获取的真实数据作为后备
    { timestamp: '2025-11-15T15:00:00', qwen: 98125, kimi: 106640, deepseek: 102233 },
    { timestamp: '2025-11-16T15:00:00', qwen: 103543, kimi: 99968, deepseek: 106424 },
    { timestamp: '2025-11-17T15:00:00', qwen: 103844, kimi: 101265, deepseek: 102885 },
  ]

  return (
    <div className="border-2 border-border flex flex-col h-full">


      <div className="p-4 border-b-2 border-border flex-shrink-0">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          收益曲线
        </h2>
      </div>
      {/* 实时图表容器 */}
      <div className="flex-1 bg-gray-50 relative p-4 overflow-hidden">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              minTickGap={30}
              interval="preserveStartEnd"
              tickFormatter={(value) => {
                try {
                  const date = new Date(value)
                  const now = new Date()
                  const isToday = date.toDateString() === now.toDateString()

                  // 如果是今天，只显示时间；否则显示日期+时间
                  if (isToday) {
                    return date.toLocaleTimeString('zh-CN', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })
                  } else {
                    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
                  }
                } catch {
                  return value
                }
              }}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={['dataMin - 1000', 'dataMax + 1000']}
              tickFormatter={(value) => `¥${(value / 1000).toFixed(1)}K`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #000',
                borderRadius: '0',
                fontSize: '12px',
                fontFamily: 'Courier New, monospace'
              }}
              formatter={(value: any) => [`¥${value.toLocaleString()}`, '']}
              labelFormatter={(label) => {
                try {
                  const date = new Date(label)
                  return date.toLocaleString('zh-CN')
                } catch {
                  return label
                }
              }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: '10px',
                fontSize: '12px',
                fontFamily: 'Courier New, monospace'
              }}
            />
            <ReferenceLine
              y={500000}
              stroke="#666666"
              strokeWidth={1}
              strokeDasharray="5 5"
              label={{ value: "初始投资 ¥500K", position: "top", fontSize: 10 }}
            />
            <Line
              type="monotone"
              dataKey="qwen"
              stroke="#6C01E1"
              strokeWidth={1.5}
              name="Qwen3-Max"
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="kimi"
              stroke="#17142E"
              strokeWidth={1.5}
              name="Kimi K2"
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="deepseek"
              stroke="#4E6CFE"
              strokeWidth={1.5}
              name="DeepSeek V3.1"
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
