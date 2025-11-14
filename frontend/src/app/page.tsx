'use client'

import { useState } from 'react'
import HoldingCurves from '@/components/HoldingCurves'
import ModelChats from '@/components/ModelChats'
import Portfolio from '@/components/Portfolio'
import Orders from '@/components/Orders'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'portfolio' | 'orders'>('portfolio')

  return (
    <div className="max-w-[95vw] mx-auto p-4 space-y-4">
      {/* Header */}
      <header className="flex justify-between items-start border-b-2 border-border pb-2">
        <div>
          <h1 className="text-xl font-bold">AI_STOCK_COMPETITION_v2.1</h1>
          <p className="text-xs text-gray-700">STATUS: [A_SHARE_MARKET_LIVE]</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-semibold">
          <button className="border border-gray-300 px-3 py-1 hover:bg-black hover:text-white transition-colors duration-150">
            SHARE_SESSION
          </button>
          <button className="border border-gray-300 px-3 py-1 hover:bg-black hover:text-white transition-colors duration-150">
            JOIN_COMP
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Left Side - 70% */}
        <main className="flex flex-col w-full lg:w-[70%] gap-4">
          {/* Holding Curves */}
          <HoldingCurves />

          {/* Model Chats */}
          <ModelChats />
        </main>

        {/* Right Side - 30% */}
        <aside className="w-full lg:w-[30%] border-2 border-border flex flex-col">
          {/* Tab Navigation */}
          <div className="flex text-sm font-semibold border-b-2 border-border">
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`flex-1 p-2 text-center uppercase tracking-wider hover:bg-black hover:text-white transition-colors duration-150 ${
                activeTab === 'portfolio' ? 'bg-black text-white' : ''
              }`}
            >
              Portfolio
            </button>
            <div className="w-px bg-gray-300"></div>
            <button
              onClick={() => setActiveTab('orders')}
              className={`flex-1 p-2 text-center uppercase tracking-wider hover:bg-black hover:text-white transition-colors duration-150 ${
                activeTab === 'orders' ? 'bg-black text-white' : ''
              }`}
            >
              Orders
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1">
            {activeTab === 'portfolio' && <Portfolio />}
            {activeTab === 'orders' && <Orders />}
          </div>
        </aside>
      </div>
    </div>
  )
}
