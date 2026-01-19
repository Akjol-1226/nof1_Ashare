import React, { useEffect, useState } from 'react';
import { Zap, Activity } from 'lucide-react';
import { Theme, TickerItem } from './types';
import { tradingWebSocket } from '@/services/websocket';

interface Props {
  theme: Theme;
}

const StockTicker: React.FC<Props> = ({ theme }) => {
  const isPop = theme === 'pop';
  const [tickerItems, setTickerItems] = useState<TickerItem[]>([]);

  useEffect(() => {
    tradingWebSocket.connect();

    const handleMessage = (data: any) => {
      if (data.type === 'trading_update' && data.data?.quotes) {
        const items: TickerItem[] = data.data.quotes.map((quote: any) => ({
          name: quote.name || quote.code,
          price: quote.price || 0,
          change: quote.change_percent || 0
        }));
        setTickerItems(items);
      }
    };

    tradingWebSocket.onMessage(handleMessage);

    return () => {
      tradingWebSocket.offMessage(handleMessage);
    };
  }, []);

  const itemsToRender = tickerItems.length > 0 ? tickerItems : [];

  if (isPop) {
    return (
      <div className="w-full bg-primary border-y-2 border-black flex items-center h-12 text-sm font-bold z-20 relative overflow-hidden">
        {/* Label Box */}
        <div className="absolute left-0 top-0 bottom-0 px-6 bg-black text-white flex items-center justify-center z-10 skew-x-[-10deg] -ml-2 border-r-4 border-white">
          <div className="skew-x-[10deg] flex items-center space-x-2">
            <Zap size={18} className="fill-current text-primary animate-pulse" />
            <span className="font-black tracking-widest uppercase">实时行情</span>
          </div>
        </div>
        <div className="whitespace-nowrap flex animate-ticker pl-32">
          {/* Repeat list 3 times for seamless loop */}
          {[...itemsToRender, ...itemsToRender, ...itemsToRender].map((item, idx) => (
            <div key={`${item.name}-${idx}`} className="flex items-center mx-8 group cursor-pointer hover:scale-110 transition-transform">
              <span className="text-black font-black mr-2 font-sans text-lg">{item.name}</span>
              <span className="text-gray-800 font-mono text-base mr-2">¥{item.price.toFixed(2)}</span>
              <span className={`px-2 py-0.5 border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] text-xs font-bold ${item.change >= 0 ? "bg-secondary text-black" : "bg-white text-black"}`}>
                {item.change >= 0 ? "▲" : "▼"}{item.change}%
              </span>
            </div>
          ))}
          {itemsToRender.length === 0 && <span className="mx-8 font-mono">Waiting for market data...</span>}
        </div>
      </div>
    );
  }

  // Glass Theme
  return (
    <div className="w-full h-14 flex items-center z-20 relative overflow-hidden glass-panel rounded-2xl mb-6 mx-auto shadow-glass-sm max-w-[98%]">
      <div className="absolute left-0 top-0 bottom-0 px-6 bg-white/80 backdrop-blur-md flex items-center justify-center z-10 border-r border-white/50">
        <div className="flex items-center space-x-2 text-indigo-600">
          <Activity size={20} className="animate-pulse" />
          <span className="font-glassHeader font-bold tracking-wide text-sm">MARKET LIVE</span>
        </div>
      </div>
      <div className="whitespace-nowrap flex pl-36 items-center h-full gap-6 overflow-x-auto">
        {itemsToRender.map((item, idx) => (
          <div key={`${item.name}-${idx}`} className="flex items-center group cursor-default">
            <span className="text-slate-800 font-glass font-semibold mr-2 text-sm">{item.name}</span>
            <span className="text-slate-500 font-mono text-sm mr-3">¥{item.price.toFixed(2)}</span>
            <span className={`px-2 py-1 rounded-full text-[10px] font-bold flex items-center ${item.change >= 0 ? "bg-emerald-100/80 text-emerald-700" : "bg-rose-100/80 text-rose-700"}`}>
              {item.change >= 0 ? "+" : ""}{item.change}%
            </span>
          </div>
        ))}
        {itemsToRender.length === 0 && <span className="mx-6 font-mono text-slate-500">Waiting for market data...</span>}
      </div>
    </div>
  );
};

export default StockTicker;

