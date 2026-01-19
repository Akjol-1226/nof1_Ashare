import React from 'react';
import { Swords, Share2, Info } from 'lucide-react';
import StockTicker from './StockTicker';
import ChartSection from './ChartSection';
import ChatSection from './ChatSection';
import Sidebar from './Sidebar';
import { Theme } from './types';

interface Props {
    theme: Theme;
}

interface Props {
    theme: Theme;
}

const NewDesignHost: React.FC<Props> = ({ theme }) => {
    const isPop = theme === 'pop';

    return (
        <div className={`h-screen overflow-hidden transition-all duration-500 flex flex-col ${isPop ? 'font-sans bg-[#E0E7FF] pb-6' : 'font-glass bg-[#F3F6FC] pb-6'}`}>

            {/* Dynamic Background for Glass Theme */}
            {!isPop && (
                <div className="fixed inset-0 z-0 pointer-events-none">
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 opacity-80"></div>
                    <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-blue-200/20 blur-[120px]"></div>
                    <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-purple-200/20 blur-[120px]"></div>
                </div>
            )}

            {/* Top Banner Warning (Conditional Style) */}
            <div className={`${isPop ? 'bg-black text-white font-mono' : 'bg-slate-900/90 backdrop-blur-md text-slate-200 font-glass tracking-wide'} text-center py-1 text-xs font-bold uppercase z-50 relative shrink-0`}>
                {isPop ? '⚠️ 自动托管模式运行中 // 禁止人类干预 ⚠️' : 'System: Autonomous Trading Mode Active // Intervention Restricted'}
            </div>

            {/* Main Container */}
            <div className="max-w-[1920px] w-full mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-2 relative z-10 flex-1 flex flex-col h-full overflow-hidden">

                {/* Header Section */}
                <header className="mb-4 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 shrink-0">
                    <div className="flex items-center space-x-4">
                        {isPop ? (
                            <div className="w-12 h-12 bg-primary border-4 border-black shadow-hard flex items-center justify-center transform rotate-3 hover:rotate-6 transition-transform">
                                <Swords size={24} className="text-black" />
                            </div>
                        ) : (
                            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-lg shadow-blue-500/30 flex items-center justify-center text-white">
                                <Swords size={20} />
                            </div>
                        )}

                        <div>
                            <h1 className={`text-2xl md:text-3xl tracking-tighter uppercase ${isPop ? 'font-black text-black italic drop-shadow-sm' : 'font-glassHeader font-bold text-slate-800'}`} style={isPop ? { textShadow: '2px 2px 0 #fff' } : {}}>
                                {isPop ? 'AI 股神争霸赛' : 'AI Trading League'}
                            </h1>
                            <p className={`text-[10px] font-bold inline-block px-2 ${isPop ? 'font-mono bg-white border-2 border-black shadow-hard-sm text-black' : 'font-glass text-slate-500 bg-white/50 rounded-lg backdrop-blur-sm mt-1'}`}>
                                {isPop ? '第一届 // 2024赛季' : 'Season 2024 // Neural Finance'}
                            </p>
                        </div>
                    </div>

                    <div className={`flex space-x-4 ${isPop ? '' : 'hidden md:flex'}`}>
                        <button className={`px-4 py-1.5 transition-all flex items-center gap-2 text-sm ${isPop ? 'bg-white border-4 border-black shadow-hard font-black hover:translate-y-1 hover:shadow-hard-sm' : 'glass-panel rounded-xl text-slate-600 font-glass font-semibold hover:bg-white/80'}`}>
                            <Share2 size={16} />
                            {isPop ? '分享' : 'Share'}
                        </button>
                        <button className={`px-4 py-1.5 transition-all flex items-center gap-2 text-sm ${isPop ? 'bg-accent border-4 border-black shadow-hard font-black hover:translate-y-1 hover:shadow-hard-sm' : 'glass-panel rounded-xl text-slate-600 font-glass font-semibold hover:bg-white/80'}`}>
                            <Info size={16} />
                            {isPop ? '规则' : 'Rules'}
                        </button>
                    </div>
                </header>

                {/* Ticker Bar */}
                <div className={`mb-4 transition-transform duration-300 shrink-0 ${isPop ? 'transform -rotate-1 hover:rotate-0' : ''}`}>
                    <StockTicker theme={theme} />
                </div>

                {/* Game Grid - Main Layout Adjustment */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 overflow-hidden h-full pb-4">

                    {/* Left Column (Main Content) - Approx 70% width */}
                    <div className="lg:col-span-8 flex flex-col gap-4 h-full overflow-hidden">
                        {/* Top: Chart Section - 60% */}
                        <div className="flex-[6] overflow-hidden min-h-0">
                            <ChartSection theme={theme} />
                        </div>

                        {/* Bottom: Chat Section - 40% */}
                        <div className="flex-[4] overflow-hidden min-h-0">
                            <ChatSection theme={theme} />
                        </div>
                    </div>

                    {/* Right Column (Sidebar/Portfolio) - Approx 30% width */}
                    <div className="lg:col-span-4 h-full overflow-hidden min-h-0">
                        <Sidebar theme={theme} />
                    </div>

                </div>

            </div>
        </div>
    );
};

export default NewDesignHost;
