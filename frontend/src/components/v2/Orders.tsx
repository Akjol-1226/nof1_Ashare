import React, { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { tradingWebSocket } from '@/services/websocket';
import { Theme } from './types';
import { Order as BaseOrderType } from '@/types'; // Import base type

interface Props {
    theme: Theme;
}

interface DisplayOrder {
    ai_name: string;
    side: string;
    symbol: string;
    quantity: number;
    price: number;
    status: string;
}

const Orders: React.FC<Props> = ({ theme }) => {
    const isPop = theme === 'pop';
    const [orders, setOrders] = useState<DisplayOrder[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // 1. Fetch initial API data
        const fetchOrders = async () => {
            try {
                setLoading(true);
                const data = await apiService.getAllOrders();
                const formatted = (data || []).map((o: any) => formatOrder(o));
                setOrders(formatted);
            } catch (e) {
                console.error("Failed to fetch orders:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchOrders();

        // 2. Listen to WebSocket
        // Note: 'tradingWebSocket' is a singleton instance
        const handleMessage = (msg: any) => {
            if (msg.type === 'trading_update' && msg.data?.orders) {
                const formatted = msg.data.orders.map((o: any) => formatOrder(o));
                setOrders(formatted);
            }
        };

        // We assume tradingWebSocket is already connected by Sidebar or App component,
        // but adding a listener here is fine.
        tradingWebSocket.onMessage(handleMessage);

        return () => {
            // tradingWebSocket.offMessage(handleMessage); // If offMessage exists? 
            // The original Sidebar.tsx doesn't remove listener, maybe the service handles multiple listeners?
            // The Original Orders.tsx does: tradingWebSocket.offMessage(handleMessage)
            // Let's assume we can just leave it or if we had an off method.
            // The provided code snippet for Sidebar doesn't show an 'off' method being used in return,
            // but Orders.tsx does: tradingWebSocket.offMessage(handleMessage)
        };
    }, []);

    const formatOrder = (order: any): DisplayOrder => ({
        ai_name: order.ai_name,
        side: (order.direction || '').toUpperCase(),
        symbol: order.stock_name || order.stock_code,
        quantity: order.quantity,
        price: order.price,
        status: (order.status || '').charAt(0).toUpperCase() + (order.status || '').slice(1)
    });

    if (loading) return <div className={`p-4 text-center ${isPop ? 'font-mono' : 'font-glass'} text-gray-400`}>Loading orders...</div>;

    if (!loading && orders.length === 0) {
        return <div className={`p-4 text-center ${isPop ? 'font-mono' : 'font-glass'} text-gray-400`}>No recent orders</div>;
    }

    // Pop Theme (Brutalist)
    if (isPop) {
        return (
            <div className="h-full overflow-y-auto pr-2 pb-4 space-y-3">
                {orders.map((o, i) => (
                    <div key={i} className="border-2 border-black p-3 bg-white shadow-hard-sm relative group hover:translate-x-1 transition-transform">
                        <div className="flex justify-between items-start mb-2">
                            <div className="font-black text-sm">{o.ai_name}</div>
                            <div className={`font-black text-xs px-2 py-0.5 border border-black ${o.side === 'BUY' ? 'bg-green-300' : 'bg-red-300'}`}>
                                {o.side}
                            </div>
                        </div>
                        <div className="flex justify-between items-center text-xs font-mono font-bold mb-2">
                            <div>{o.symbol}</div>
                            <div className="text-right">
                                <div>{o.quantity} shares</div>
                                <div>{o.price != null ? `@${o.price.toFixed(2)}` : '市价'}</div>
                            </div>
                        </div>
                        <div className="flex justify-end">
                            <span className={`text-[10px] font-bold uppercase tracking-wider ${o.status === 'Filled' ? 'text-green-700' :
                                o.status === 'Rejected' ? 'text-red-700' : 'text-gray-500'
                                }`}>
                                [{o.status}]
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    // Glass Theme
    return (
        <div className="h-full overflow-y-auto pr-1 pb-4 scrollbar-hide">
            <div className="space-y-2">
                {orders.map((o, i) => (
                    <div key={i} className="bg-white/40 hover:bg-white/60 backdrop-blur-sm p-3 rounded-xl transition-all border border-white/50 shadow-sm">
                        <div className="flex justify-between items-center mb-2">
                            <div className="flex items-center space-x-2">
                                <span className={`w-1.5 h-1.5 rounded-full ${o.side === 'BUY' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                                <span className="font-glassHeader font-bold text-slate-700 text-sm">{o.ai_name}</span>
                            </div>
                            <span className={`text-[10px] font-bold px-2 py-1 rounded-lg ${o.status === 'Filled' ? 'bg-emerald-100/50 text-emerald-700' :
                                o.status === 'Rejected' ? 'bg-rose-100/50 text-rose-700' : 'bg-slate-100/50 text-slate-600'
                                }`}>
                                {o.status}
                            </span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                            <div className="font-medium text-slate-600">{o.symbol}</div>
                            <div className="text-right font-mono text-slate-500">
                                <span className={o.side === 'BUY' ? 'text-emerald-600' : 'text-rose-600'}>{o.side}</span>
                                <span className="mx-1">·</span>
                                {o.quantity} @ {o.price != null ? o.price.toFixed(2) : '市价'}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Orders;
