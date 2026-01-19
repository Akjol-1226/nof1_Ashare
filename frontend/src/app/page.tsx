'use client'

import { useState } from 'react'
import HoldingCurves from '@/components/HoldingCurves'
import ModelChats from '@/components/ModelChats'
import Portfolio from '@/components/Portfolio'
import Orders from '@/components/Orders'
import StockTickerBar from '@/components/StockTickerBar'
import NewDesignHost from '@/components/v2/NewDesignHost'
import { Layout, Palette, MonitorPlay } from 'lucide-react'

function OldHome() {
  const [activeTab, setActiveTab] = useState<'portfolio' | 'orders'>('portfolio')

  return (
    <div className="max-w-[95vw] mx-auto p-4 h-screen flex flex-col overflow-hidden bg-white">
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

      {/* Stock Ticker Bar */}
      <StockTickerBar />

      {/* Main Content - Fill remaining space */}
      <div className="flex flex-col lg:flex-row gap-4 mt-4 flex-1 overflow-hidden">
        {/* Left Side - 70% */}
        <main className="flex flex-col w-full lg:w-[70%] gap-4 flex-1 overflow-hidden">
          {/* Holding Curves - 60% of remaining space */}
          <div className="flex-[6] overflow-hidden">
            <HoldingCurves />
          </div>

          {/* Model Chats - 40% of remaining space */}
          <div className="flex-[4] overflow-hidden">
            <ModelChats />
          </div>
        </main>

        {/* Right Side - 30% - Match left side height */}
        <aside className="w-full lg:w-[30%] border-2 border-border flex flex-col overflow-hidden">
          {/* Tab Navigation */}
          <div className="flex text-sm font-semibold border-b-2 border-border">
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`flex-1 p-2 text-center uppercase tracking-wider hover:bg-black hover:text-white transition-colors duration-150 ${activeTab === 'portfolio' ? 'bg-black text-white' : ''
                }`}
            >
              Portfolio
            </button>
            <div className="w-px bg-gray-300"></div>
            <button
              onClick={() => setActiveTab('orders')}
              className={`flex-1 p-2 text-center uppercase tracking-wider hover:bg-black hover:text-white transition-colors duration-150 ${activeTab === 'orders' ? 'bg-black text-white' : ''
                }`}
            >
              Orders
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'portfolio' && <Portfolio />}
            {activeTab === 'orders' && <Orders />}
          </div>
        </aside>
      </div>
    </div>
  )
}

export default function Home() {
  const [activeStyle, setActiveStyle] = useState<'original' | 'pop' | 'glass'>('original');

  return (
    <div className="relative">
      {/* Centralized Style Switcher */}
      <div className="fixed bottom-6 left-6 z-[100] flex flex-col-reverse gap-2 group items-start">
        <div className="bg-black text-white px-4 py-2 rounded-full font-bold shadow-lg flex items-center gap-2 border-2 border-white cursor-pointer group-hover:scale-105 transition-transform w-[200px] justify-between">
          <div className="flex items-center gap-2">
            <Palette size={16} />
            <span>Change Style</span>
          </div>
          <span className="text-xs text-gray-400 capitalize">{activeStyle}</span>
        </div>

        {/* Dropup Menu */}
        <div className="flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none group-hover:pointer-events-auto transform translate-y-2 group-hover:translate-y-0 duration-200">
          <button
            onClick={() => setActiveStyle('original')}
            className={`px-4 py-2 rounded-full font-bold shadow-lg text-left text-sm border-2 w-[200px] ${activeStyle === 'original' ? 'bg-gray-800 text-white border-white' : 'bg-white text-black border-black hover:bg-gray-100'}`}
          >
            Original (Classic)
          </button>
          <button
            onClick={() => setActiveStyle('pop')}
            className={`px-4 py-2 rounded-full font-bold shadow-lg text-left text-sm border-2 w-[200px] ${activeStyle === 'pop' ? 'bg-indigo-600 text-white border-white' : 'bg-white text-black border-black hover:bg-indigo-50'}`}
          >
            New Design (Pop)
          </button>
          <button
            onClick={() => setActiveStyle('glass')}
            className={`px-4 py-2 rounded-full font-bold shadow-lg text-left text-sm border-2 w-[200px] ${activeStyle === 'glass' ? 'bg-slate-600 text-white border-white' : 'bg-white text-black border-black hover:bg-slate-50'}`}
          >
            New Design (Glass)
          </button>
        </div>
      </div>

      {activeStyle === 'original' && <OldHome />}
      {activeStyle === 'pop' && <NewDesignHost theme="pop" />}
      {activeStyle === 'glass' && <NewDesignHost theme="glass" />}
    </div>
  );
}
