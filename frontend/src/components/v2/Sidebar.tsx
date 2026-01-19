import React, { useState, useEffect } from 'react';
import { Trophy, TrendingUp, TrendingDown, Award, PieChart, List } from 'lucide-react';
import { Theme, AiModel, Stock } from './types';
import { apiService } from '@/services/api';
import { tradingWebSocket } from '@/services/websocket';
import { AI_MODELS as MOCK_MODELS } from './constants'; // Use for color reference
import Orders from './Orders';

interface Props {
    theme: Theme;
}

const Sidebar: React.FC<Props> = ({ theme }) => {
    const isPop = theme === 'pop';
    const [activeTab, setActiveTab] = useState<'portfolio' | 'orders'>('portfolio');
    const [models, setModels] = useState<AiModel[]>([]);

    useEffect(() => {
        // 1. Initial Fetch
        const fetchInitialData = async () => {
            try {
                const rankings = await apiService.getAIRanking();
                const formatted = rankings.map((r: any) => mapToAiModel(r));
                setModels(formatted);
            } catch (e) {
                console.error("Failed to fetch initial portfolio data:", e);
            }
        };
        fetchInitialData();

        // 2. WebSocket
        tradingWebSocket.connect();
        const handleMessage = (message: any) => {
            if (message.type === 'trading_update' && message.data?.portfolios) {
                const formatted = message.data.portfolios.map((p: any) => mapToAiModel(p));
                setModels(formatted);
            }
        };

        tradingWebSocket.onMessage(handleMessage);

        return () => {
            // cleanup?
        };
    }, []);

    const mapToAiModel = (data: any): AiModel => {
        // Try to find static metadata (color, avatar)
        const nameLower = (data.ai_name || '').toLowerCase();
        let staticMeta = MOCK_MODELS.find(m => nameLower.includes(m.id));
        if (!staticMeta) {
            if (nameLower.includes('qwen')) staticMeta = MOCK_MODELS.find(m => m.id === 'qwen');
            else if (nameLower.includes('deepseek')) staticMeta = MOCK_MODELS.find(m => m.id === 'deepseek');
            else if (nameLower.includes('kimi')) staticMeta = MOCK_MODELS.find(m => m.id === 'kimi');
            else if (nameLower.includes('gpt')) staticMeta = MOCK_MODELS.find(m => m.id === 'gpt4');
            else if (nameLower.includes('claude')) staticMeta = MOCK_MODELS.find(m => m.id === 'claude');
        }

        // Map positions
        const holdings: Stock[] = (data.positions || []).map((pos: any) => ({
            symbol: pos.stock_code,
            name: pos.stock_name || pos.stock_code,
            price: pos.current_price,
            change: pos.profit_loss_percent, // Use profit % as change for now
            shares: pos.quantity,
            available: pos.available_quantity || 0,
            avgCost: pos.avg_cost || 0,
            profit: pos.profit_loss || 0
        }));

        return {
            id: data.ai_id ? String(data.ai_id) : nameLower,
            name: data.ai_name,
            avatar: staticMeta?.avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${data.ai_name}`,
            color: staticMeta?.color || '#000',
            totalValue: data.total_assets || 0,
            totalProfit: data.profit_loss || (data.total_assets - 500000) || 0,
            pnlPercent: data.return_rate || 0,
            holdings: holdings,
            description: staticMeta?.description || 'AI Trader'
        };
    };

    const sortedModels = [...models].sort((a, b) => b.pnlPercent - a.pnlPercent);

    return (
        <div className="flex flex-col h-full overflow-hidden">

            {/* Header / Tabs */}
            {isPop ? (
                <div className="flex space-x-2 mb-4 shrink-0">
                    <button
                        onClick={() => setActiveTab('portfolio')}
                        className={`flex-1 flex items-center justify-center space-x-2 border-4 border-black p-2 shadow-hard font-black uppercase text-sm transition-transform hover:-translate-y-1 ${activeTab === 'portfolio' ? 'bg-primary text-black' : 'bg-white text-gray-400'}`}
                    >
                        <PieChart size={18} />
                        <span>持仓</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('orders')}
                        className={`flex-1 flex items-center justify-center space-x-2 border-4 border-black p-2 shadow-hard font-black uppercase text-sm transition-transform hover:-translate-y-1 ${activeTab === 'orders' ? 'bg-secondary text-black' : 'bg-white text-gray-400'}`}
                    >
                        <List size={18} />
                        <span>订单</span>
                    </button>
                </div>
            ) : (
                <div className="glass-panel rounded-2xl p-1 mb-4 flex shrink-0 shadow-glass-sm">
                    <button
                        onClick={() => setActiveTab('portfolio')}
                        className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-xl text-sm font-glassHeader font-bold transition-all ${activeTab === 'portfolio' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-400 hover:text-slate-600'}`}
                    >
                        <span>Portfolio</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('orders')}
                        className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-xl text-sm font-glassHeader font-bold transition-all ${activeTab === 'orders' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-400 hover:text-slate-600'}`}
                    >
                        <span>Orders</span>
                    </button>
                </div>
            )}

            {/* Ranked List */}
            <div className="overflow-y-auto pb-4 scrollbar-hide space-y-4 flex-1">
                {activeTab === 'orders' ? (
                    <Orders theme={theme} />
                ) : (
                    sortedModels.map((model, index) => {
                        if (isPop) {
                            return (
                                <div key={model.id} className="brutalist-card p-4 relative group cursor-pointer bg-white">
                                    <div className={`absolute -top-3 -left-3 w-8 h-8 flex items-center justify-center border-2 border-black font-black text-lg shadow-hard-sm z-10 
                    ${index === 0 ? 'bg-yellow-400' : index === 1 ? 'bg-gray-300' : index === 2 ? 'bg-orange-400' : 'bg-white'}`}>
                                        {index + 1}
                                    </div>

                                    {/* Header Info */}
                                    <div className="flex justify-between items-start mb-3 pl-2">
                                        <div className="flex items-center space-x-3">
                                            <img src={model.avatar} className="w-10 h-10 border-2 border-black bg-gray-50" />
                                            <div>
                                                <h3 className="font-black text-lg leading-none">{model.name}</h3>
                                                <div className="font-mono font-bold text-sm mt-1">¥{(model.totalValue).toLocaleString()}</div>
                                            </div>
                                        </div>
                                        <div className={`flex flex-col items-end`}>
                                            <div className={`flex items-center space-x-1 px-2 py-0.5 border-2 border-black text-xs font-bold shadow-[2px_2px_0px_0px_#000]
                        ${model.totalProfit >= 0 ? 'bg-danger text-white' : 'bg-success text-white'}`}>
                                                {model.totalProfit >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                                                <span>{model.totalProfit >= 0 ? '+' : ''}{model.pnlPercent.toFixed(2)}%</span>
                                            </div>
                                            <div className={`text-xs font-bold mt-1 ${model.totalProfit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                {model.totalProfit >= 0 ? '+' : ''}¥{model.totalProfit.toLocaleString()}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Detailed Holdings Table (Classic Fields) */}
                                    <div className="border-t-2 border-black pt-2 pl-2">
                                        <table className="w-full text-[10px] font-mono">
                                            <thead>
                                                <tr className="text-gray-500 border-b border-black/20">
                                                    <th className="text-left pb-1">名称/代码</th>
                                                    <th className="text-right pb-1">持股/可用</th>
                                                    <th className="text-right pb-1">现价/成本</th>
                                                    <th className="text-right pb-1">盈亏/比率</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {model.holdings.map((stock) => (
                                                    <tr key={stock.symbol} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                                                        <td className="py-1">
                                                            <div className="font-bold">{stock.name}</div>
                                                            <div className="text-gray-400">{stock.symbol}</div>
                                                        </td>
                                                        <td className="text-right py-1">
                                                            <div>{stock.shares}</div>
                                                            <div className="text-gray-400">{stock.available}</div>
                                                        </td>
                                                        <td className="text-right py-1">
                                                            <div>{stock.price.toFixed(2)}</div>
                                                            <div className="text-gray-400">{stock.avgCost.toFixed(2)}</div>
                                                        </td>
                                                        <td className={`text-right py-1 font-bold ${stock.profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                            <div>{stock.profit >= 0 ? '+' : ''}¥{stock.profit.toFixed(2)}</div>
                                                            <div className="text-gray-400">{stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%</div>
                                                        </td>
                                                    </tr>
                                                ))}
                                                {model.holdings.length === 0 && (
                                                    <tr>
                                                        <td colSpan={4} className="text-center py-2 text-gray-400 italic">No Positions</td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            );
                        } else {
                            // Glass Theme Card
                            return (
                                <div key={model.id} className="glass-card p-4 rounded-2xl relative mb-4 transition-all hover:bg-white/90">
                                    {/* Header Info */}
                                    <div className="flex items-center space-x-4 mb-4">
                                        <div className="relative">
                                            <img src={model.avatar} className="w-12 h-12 rounded-2xl shadow-sm bg-white" />
                                            <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white flex items-center justify-center text-[8px] font-bold text-white shadow-sm" style={{ backgroundColor: model.color }}>
                                                AI
                                            </div>
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h3 className="font-glassHeader font-bold text-slate-800 text-base">{model.name}</h3>
                                                    <div className="text-xs text-slate-500 font-glass">总资产: <span className="font-mono text-slate-700 font-bold">¥{model.totalValue.toLocaleString()}</span></div>
                                                </div>
                                                <div className={`text-right ${model.totalProfit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                    <div className="font-bold text-sm font-mono">{model.totalProfit >= 0 ? "+" : ""}¥{model.totalProfit.toLocaleString()}</div>
                                                    <div className="text-[10px]">{model.pnlPercent >= 0 ? "+" : ""}{model.pnlPercent.toFixed(2)}%</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Detailed Holdings Table (Glass Style) */}
                                    <div className="bg-slate-50/50 rounded-xl p-2 border border-slate-100">
                                        <table className="w-full text-[10px]">
                                            <thead>
                                                <tr className="text-slate-400 font-glass">
                                                    <th className="text-left pb-2 font-medium">名称/代码</th>
                                                    <th className="text-right pb-2 font-medium">持股/可用</th>
                                                    <th className="text-right pb-2 font-medium">现价/成本</th>
                                                    <th className="text-right pb-2 font-medium">盈亏/比率</th>
                                                </tr>
                                            </thead>
                                            <tbody className="font-mono text-slate-600">
                                                {model.holdings.map((stock) => (
                                                    <tr key={stock.symbol} className="border-b border-slate-100/50 last:border-0 hover:bg-white/50">
                                                        <td className="py-1.5">
                                                            <div className="font-semibold text-slate-700">{stock.name}</div>
                                                            <div className="text-slate-400 text-[9px]">{stock.symbol}</div>
                                                        </td>
                                                        <td className="text-right py-1.5">
                                                            <div>{stock.shares}</div>
                                                            <div className="text-slate-400 text-[9px]">{stock.available}</div>
                                                        </td>
                                                        <td className="text-right py-1.5">
                                                            <div>{stock.price.toFixed(2)}</div>
                                                            <div className="text-slate-400 text-[9px]">{stock.avgCost.toFixed(2)}</div>
                                                        </td>
                                                        <td className={`text-right py-1.5 font-bold ${stock.profit >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                                                            <div>{stock.profit >= 0 ? '+' : ''}¥{stock.profit.toFixed(2)}</div>
                                                            <div className="text-slate-400 text-[9px]">{stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%</div>
                                                        </td>
                                                    </tr>
                                                ))}
                                                {model.holdings.length === 0 && (
                                                    <tr>
                                                        <td colSpan={4} className="text-center py-3 text-slate-400">Empty Portfolio</td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            );
                        }
                    }))}
            </div>
        </div>
    );
};

export default Sidebar;
