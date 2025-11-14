'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

// 模拟数据 - 后续会从WebSocket获取
// 注意：时间是连续的，没有休市断点
const mockData = [
  { time: '09:30', date: '10/14', qwen: 100000, kimi: 100000, deepseek: 100000 },
  { time: '10:00', date: '10/14', qwen: 101200, kimi: 99500, deepseek: 102100 },
  { time: '10:30', date: '10/14', qwen: 100800, kimi: 101500, deepseek: 101800 },
  { time: '11:00', date: '10/14', qwen: 102500, kimi: 100200, deepseek: 103200 },
  { time: '11:30', date: '10/14', qwen: 101800, kimi: 102100, deepseek: 102900 },
  // 注意：这里直接跳到13:00，没有12:00的空隙
  { time: '13:00', date: '10/14', qwen: 103100, kimi: 101800, deepseek: 104200 },
  { time: '13:30', date: '10/14', qwen: 102700, kimi: 103500, deepseek: 103800 },
  { time: '14:00', date: '10/14', qwen: 103100, kimi: 101800, deepseek: 104200 },
  { time: '14:30', date: '10/14', qwen: 102700, kimi: 103500, deepseek: 103800 },
  { time: '15:00', date: '10/14', qwen: 104200, kimi: 102900, deepseek: 105100 },
  // 第二天
  { time: '09:30', date: '10/15', qwen: 104500, kimi: 103100, deepseek: 105300 },
]

// 简单SVG图表组件
function SimpleLineChart({ data }: { data: any[] }) {
  const width = 600
  const height = 200
  const padding = 40

  // 数据范围
  const minValue = 95000
  const maxValue = 106000
  const baseline = 100000

  // 坐标转换函数
  const xScale = (index: number) => (index / (data.length - 1)) * (width - 2 * padding) + padding
  const yScale = (value: number) => height - padding - ((value - minValue) / (maxValue - minValue)) * (height - 2 * padding)

  // 生成路径
  const createPath = (key: string) => {
    return data.map((point, index) => {
      const x = xScale(index)
      const y = yScale(point[key])
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    }).join(' ')
  }

  return (
    <div className="w-full">
      <svg width={width} height={height} className="border border-gray-200">
        {/* 网格线 */}
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* 基准线 */}
        <line
          x1={padding}
          y1={yScale(baseline)}
          x2={width - padding}
          y2={yScale(baseline)}
          stroke="#666"
          strokeWidth="1"
          strokeDasharray="5,5"
        />
        <text x={padding + 10} y={yScale(baseline) - 5} fontSize="10" fill="#666">
          基准线 ¥100K
        </text>

        {/* Y轴标签 */}
        <text x={10} y={yScale(maxValue) + 5} fontSize="10" fill="#666">¥106K</text>
        <text x={10} y={yScale(baseline) + 5} fontSize="10" fill="#666">¥100K</text>
        <text x={10} y={yScale(minValue) + 5} fontSize="10" fill="#666">¥95K</text>

        {/* X轴标签 */}
        {data.map((point, index) => (
          <text
            key={index}
            x={xScale(index)}
            y={height - 10}
            fontSize="10"
            fill="#666"
            textAnchor="middle"
          >
            {point.date} {point.time}
          </text>
        ))}

        {/* 数据线 */}
        <path
          d={createPath('qwen')}
          fill="none"
          stroke="#3B82F6"
          strokeWidth="2"
        />
        <path
          d={createPath('kimi')}
          fill="none"
          stroke="#10B981"
          strokeWidth="2"
        />
        <path
          d={createPath('deepseek')}
          fill="none"
          stroke="#8B5CF6"
          strokeWidth="2"
        />

        {/* 图例 */}
        <g transform={`translate(${width - 120}, 20)`}>
          <circle cx="0" cy="0" r="3" fill="#3B82F6" />
          <text x="10" y="4" fontSize="10">Qwen3-Max</text>
          <circle cx="0" cy="15" r="3" fill="#10B981" />
          <text x="10" y="19" fontSize="10">Kimi K2</text>
          <circle cx="0" cy="30" r="3" fill="#8B5CF6" />
          <text x="10" y="34" fontSize="10">DeepSeek V3.1</text>
        </g>
      </svg>
    </div>
  )
}

export default function HoldingCurves() {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    console.log('HoldingCurves component client-side rendering')
    console.log('Mock data:', mockData)
  }, [])

  return (
    <div className="border-2 border-border flex-grow flex flex-col">
      <div className="p-4 border-b-2 border-border">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          HOLDING_CURVES
        </h2>
        <div className="flex items-center gap-2 mt-2">
          <div className="flex -space-x-2">
            <div className="w-6 h-6 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-medium text-white">
              Q
            </div>
            <div className="w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-medium text-white">
              K
            </div>
            <div className="w-6 h-6 bg-purple-500 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-medium text-white">
              D
            </div>
            <div className="w-6 h-6 flex items-center justify-center bg-gray-200 border-2 border-white text-[10px] font-medium text-gray-800">
              +1
            </div>
          </div>
          <span className="text-xs text-gray-700">| Active Models</span>
        </div>
      </div>
      {/* 图表容器 - 按照nof1.ai风格设计 */}
      <div className="flex-grow bg-gray-50 relative">
        {/* 图表SVG - 紧凑设计 */}
        <svg width="100%" height="100%" viewBox="0 0 900 400" className="w-full h-full">
          {/* 背景 */}
          <rect width="100%" height="100%" fill="#fafafa" />

          {/* 绘图区域边距设置 */}
          <g transform="translate(80, 60)">
            {/* 网格线 - 浅灰色背景网格 */}
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(0,0,0,0.1)" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="720" height="280" fill="url(#grid)" />

            {/* Y轴 - 金额轴 */}
            {/* 主轴线 */}
            <line x1="0" y1="0" x2="0" y2="280" stroke="rgba(0,0,0,0.4)" strokeWidth="1.5" shapeRendering="crispEdges" />

            {/* Y轴刻度线和标签 - 从上到下资产增加 */}
            <g>
              {/* ¥103K (最高) */}
              <line x1="-8" y1="0" x2="0" y2="0" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="-15" y="5" textAnchor="end" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="600" fill="rgba(0,0,0,0.8)">¥103K</text>

              {/* ¥102K */}
              <line x1="-8" y1="56" x2="0" y2="56" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="-15" y="61" textAnchor="end" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="600" fill="rgba(0,0,0,0.8)">¥102K</text>

              {/* ¥101K */}
              <line x1="-8" y1="112" x2="0" y2="112" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="-15" y="117" textAnchor="end" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="600" fill="rgba(0,0,0,0.8)">¥101K</text>

              {/* ¥100K (基准线) */}
              <line x1="-8" y1="168" x2="0" y2="168" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="-15" y="173" textAnchor="end" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="600" fill="rgba(0,0,0,0.8)">¥100K</text>

              {/* ¥99K */}
              <line x1="-8" y1="224" x2="0" y2="224" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="-15" y="229" textAnchor="end" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="600" fill="rgba(0,0,0,0.8)">¥99K</text>

              {/* ¥98K (最低) */}
              <line x1="-8" y1="280" x2="0" y2="280" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="-15" y="285" textAnchor="end" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="600" fill="rgba(0,0,0,0.8)">¥98K</text>
            </g>

            {/* X轴 - 时间轴 */}
            {/* 主轴线 */}
            <line x1="0" y1="280" x2="720" y2="280" stroke="rgba(0,0,0,0.4)" strokeWidth="1.5" shapeRendering="crispEdges" />

            {/* X轴刻度线和标签 - 3天数据 */}
            <g>
              {/* Day 1 - 09:30 */}
              <line x1="0" y1="280" x2="0" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="0" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">10/14 09:30</text>

              {/* Day 1 - 11:30 */}
              <line x1="90" y1="280" x2="90" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="90" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">11:30</text>

              {/* Day 1 - 15:00 */}
              <line x1="180" y1="280" x2="180" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="180" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">15:00</text>

              {/* Day 2 - 09:30 */}
              <line x1="270" y1="280" x2="270" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="270" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">10/15 09:30</text>

              {/* Day 2 - 11:30 */}
              <line x1="360" y1="280" x2="360" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="360" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">11:30</text>

              {/* Day 2 - 15:00 */}
              <line x1="450" y1="280" x2="450" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="450" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">15:00</text>

              {/* Day 3 - 09:30 */}
              <line x1="540" y1="280" x2="540" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="540" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">10/16 09:30</text>

              {/* Day 3 - 11:30 */}
              <line x1="630" y1="280" x2="630" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="630" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">11:30</text>

              {/* Day 3 - 15:00 */}
              <line x1="720" y1="280" x2="720" y2="288" stroke="rgba(0,0,0,0.6)" strokeWidth="1.5" shapeRendering="crispEdges" />
              <text x="720" y="305" textAnchor="middle" fontFamily="'IBM Plex Mono', monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.8)">15:00</text>
            </g>

            {/* 基准线 - ¥100K 初始投资 */}
            <line x1="0" y1="168" x2="720" y2="168" stroke="#000" strokeWidth="1" strokeDasharray="5,5" opacity="0.6" />
            <text x="10" y="163" fontFamily="'Courier New', Courier, monospace" fontSize="10" fontWeight="600" fill="rgba(0,0,0,0.7)">基准线 ¥100K</text>

            {/* 数据线条 - 3天模拟数据 */}
            {/* Qwen3-Max (#6C01E1 紫色) - 表现稳定增长 */}
            <polyline
              points="0,180 90,175 180,170 270,160 360,155 450,145 540,135 630,125 720,115"
              fill="none"
              stroke="#6C01E1"
              strokeWidth="2.5"
              shapeRendering="crispEdges"
              strokeLinecap="square"
              strokeLinejoin="round"
            />

            {/* Kimi K2 (#17142E 深紫色) - 波动较大 */}
            <polyline
              points="0,168 90,185 180,160 270,175 360,155 450,170 540,150 630,165 720,140"
              fill="none"
              stroke="#17142E"
              strokeWidth="2.5"
              strokeDasharray="8,4"
              shapeRendering="crispEdges"
              strokeLinecap="square"
              strokeLinejoin="round"
            />

            {/* DeepSeek V3.1 (#4E6CFE 蓝色) - 最佳表现 */}
            <polyline
              points="0,168 90,155 180,140 270,125 360,110 450,95 540,80 630,65 720,50"
              fill="none"
              stroke="#4E6CFE"
              strokeWidth="2.5"
              strokeDasharray="2,2"
              shapeRendering="crispEdges"
              strokeLinecap="square"
              strokeLinejoin="round"
            />
          </g>

          {/* 图例 - 右上角 */}
          <g transform="translate(650, 20)">
            {/* Qwen3-Max */}
            <line x1="0" y1="6" x2="15" y2="6" stroke="#6C01E1" strokeWidth="2.5" shapeRendering="crispEdges" />
            <text x="20" y="10" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="700" fill="#000">Qwen3-Max</text>

            {/* Kimi K2 */}
            <line x1="0" y1="24" x2="15" y2="24" stroke="#17142E" strokeWidth="2.5" strokeDasharray="8,4" shapeRendering="crispEdges" />
            <text x="20" y="28" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="700" fill="#000">Kimi K2</text>

            {/* DeepSeek V3.1 */}
            <line x1="0" y1="42" x2="15" y2="42" stroke="#4E6CFE" strokeWidth="2.5" strokeDasharray="2,2" shapeRendering="crispEdges" />
            <text x="20" y="46" fontFamily="'Courier New', Courier, monospace" fontSize="11" fontWeight="700" fill="#000">DeepSeek V3.1</text>

            {/* 当前时间和总资产 - 模拟数据 */}
            <text x="0" y="65" fontFamily="'Courier New', Courier, monospace" fontSize="9" fill="#666">2025/11/16 15:00:00</text>
            <text x="0" y="78" fontFamily="'Courier New', Courier, monospace" fontSize="13" fontWeight="700" fill="#000">¥103,200</text>
          </g>

          {/* 水印 - 右下角 */}
          <g transform="translate(780, 360)" opacity="0.25">
            <text fontFamily="'Courier New', Courier, monospace" fontSize="16" fontWeight="700" fill="#000">nof1.ai</text>
          </g>
        </svg>
      </div>
    </div>
  )
}
