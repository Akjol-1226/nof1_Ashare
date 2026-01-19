import React, { useEffect, useState } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    AreaChart,
    Area
} from 'recharts';
import { AI_MODELS } from './constants';
import { Theme } from './types';
import { performanceWebSocket } from '@/services/websocket';

interface Props {
    theme: Theme;
}

const CustomTooltip = ({ active, payload, label, theme }: any) => {
    if (active && payload && payload.length) {
        if (theme === 'pop') {
            return (
                <div className="bg-white border-2 border-black shadow-hard p-3 font-mono text-xs">
                    <p className="bg-black text-white px-2 py-1 mb-2 font-bold inline-block">TIME: {label}</p>
                    {payload.map((p: any) => (
                        <div key={p.name} className="flex justify-between items-center w-48 mb-1">
                            <div className="flex items-center space-x-2">
                                <span className="font-bold text-black uppercase">{p.name}</span>
                            </div>
                            <span className="font-bold text-black">¥{p.value.toLocaleString()}</span>
                        </div>
                    ))}
                </div>
            );
        } else {
            return (
                <div className="bg-white/80 backdrop-blur-xl border border-white/50 p-4 rounded-xl shadow-glass text-xs font-glass">
                    <p className="text-slate-400 font-medium mb-3 uppercase tracking-wider text-[10px]">Time: {label}</p>
                    {payload.map((p: any) => (
                        <div key={p.name} className="flex justify-between items-center w-40 mb-2 last:mb-0">
                            <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }}></div>
                                <span className="font-medium text-slate-700">{p.name}</span>
                            </div>
                            <span className="font-mono text-slate-600 font-medium">¥{p.value.toLocaleString()}</span>
                        </div>
                    ))}
                </div>
            );
        }
    }
    return null;
};

const ChartSection: React.FC<Props> = ({ theme }) => {
    const isPop = theme === 'pop';
    const [chartData, setChartData] = useState<any[]>([]);

    useEffect(() => {
        performanceWebSocket.connect();

        performanceWebSocket.onMessage((data: any) => {
            if (data.type === 'performance_update') {
                const snapshots = data.data?.snapshots || [];

                // Logic COPIED from HoldingCurves.tsx to ensure identical data processing
                const timeGrouped: { [key: string]: any } = {};

                snapshots.forEach((snapshot: any) => {
                    const timestamp = snapshot.timestamp;
                    if (!timeGrouped[timestamp]) {
                        // Original HoldingCurves stores just { timestamp } here, we need the display str too maybe?
                        // HoldingCurves formats it in the TickFormatter. We can store raw timestamp here.
                        timeGrouped[timestamp] = { timestamp };
                    }

                    // Strict Lowercase matching as per HoldingCurves
                    const aiNameLower = (snapshot.ai_name || '').toLowerCase();
                    if (aiNameLower.includes('qwen')) {
                        timeGrouped[timestamp].qwen = snapshot.total_assets;
                    } else if (aiNameLower.includes('kimi')) {
                        timeGrouped[timestamp].kimi = snapshot.total_assets;
                    } else if (aiNameLower.includes('deepseek')) {
                        timeGrouped[timestamp].deepseek = snapshot.total_assets;
                    }
                });

                // Sort by time
                const result = Object.values(timeGrouped).sort((a: any, b: any) =>
                    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
                );

                // Data Filling to ensure continuity (Crucial step from HoldingCurves)
                result.forEach((item: any, index: number) => {
                    if (!item.qwen) item.qwen = index > 0 ? (result[index - 1] as any).qwen : 500000;
                    if (!item.kimi) item.kimi = index > 0 ? (result[index - 1] as any).kimi : 500000;
                    if (!item.deepseek) item.deepseek = index > 0 ? (result[index - 1] as any).deepseek : 500000;

                    // Format as in HoldingCurves.tsx:
                    // 如果是今天，只显示时间；否则显示日期+时间
                    try {
                        const date = new Date(item.timestamp);
                        const now = new Date();
                        const isToday = date.toDateString() === now.toDateString();

                        if (isToday) {
                            item.time = date.toLocaleTimeString('zh-CN', {
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        } else {
                            item.time = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
                        }
                    } catch {
                        item.time = new Date(item.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                    }
                });

                setChartData(result);
            }
        });

        return () => {
            // performanceWebSocket.disconnect();
        };
    }, []);

    // Filter valid models for which we have data keys
    // For now we hardcode qwen/kimi/deepseek as in V1
    // But utilize AI_MODELS for color lookups
    const activeModels = AI_MODELS.filter(m => ['qwen', 'kimi', 'deepseek'].includes(m.id));

    return (
        <div className={`flex flex-col h-full relative ${isPop ? 'bg-white border-4 border-black shadow-hard-lg p-1' : 'glass-panel rounded-3xl shadow-glass p-6 overflow-hidden'}`}>

            {/* Header Section */}
            {isPop ? (
                <div className="flex justify-between items-center bg-accent border-b-4 border-black p-4 mb-1">
                    <h2 className="text-2xl font-black italic tracking-tighter text-black uppercase">
                        📊 收益大对决
                    </h2>
                    <div className="flex space-x-2">
                        <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-black"></div>
                        <div className="w-4 h-4 rounded-full bg-yellow-400 border-2 border-black"></div>
                        <div className="w-4 h-4 rounded-full bg-green-500 border-2 border-black"></div>
                    </div>
                </div>
            ) : (
                <div className="flex justify-between items-end mb-4 relative z-10 shrink-0">
                    <div>
                        <h2 className="text-2xl font-glassHeader font-bold text-slate-800 tracking-tight">Performance Analytics</h2>
                        <p className="text-slate-500 text-xs font-glass mt-0.5">Real-time NAV comparison across active models</p>
                    </div>
                    {/* Ambient Glow */}
                    <div className="absolute -top-32 -right-32 w-96 h-96 bg-purple-200/40 rounded-full blur-3xl pointer-events-none"></div>
                    <div className="absolute -bottom-32 -left-32 w-96 h-96 bg-blue-200/40 rounded-full blur-3xl pointer-events-none"></div>
                </div>
            )}

            <div className={`flex-grow w-full h-full relative ${isPop ? 'bg-white p-4' : 'z-10'}`}>
                {isPop && (
                    <div className="absolute inset-0 opacity-10 pointer-events-none"
                        style={{ backgroundImage: 'linear-gradient(#000 1px, transparent 1px), linear-gradient(90deg, #000 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
                    </div>
                )}
                <ResponsiveContainer width="100%" height="100%">
                    {isPop ? (
                        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ddd" />
                            <XAxis dataKey="time" stroke="#000" tick={{ fontSize: 12, fontFamily: 'JetBrains Mono', fontWeight: 'bold' }} dy={10} />
                            <YAxis
                                stroke="#000"
                                tick={{ fontSize: 12, fontFamily: 'JetBrains Mono', fontWeight: 'bold' }}
                                dx={-5}
                                domain={['dataMin - 1000', 'dataMax + 1000']}
                                tickFormatter={(value) => `¥${(value / 1000).toFixed(1)}K`}
                            />
                            <Tooltip content={<CustomTooltip theme={theme} />} />
                            <Legend wrapperStyle={{ paddingTop: '20px', fontFamily: 'Noto Sans SC', fontWeight: 'bold' }} />
                            {activeModels.map((model) => (
                                <Line
                                    key={model.id}
                                    type="linear"
                                    dataKey={model.id}
                                    name={model.name}
                                    stroke={model.color}
                                    strokeWidth={4}
                                    dot={{ r: 4, strokeWidth: 2, stroke: '#000', fill: model.color }}
                                    activeDot={{ r: 8, stroke: '#000', strokeWidth: 3, fill: model.color }}
                                    isAnimationActive={false}
                                />
                            ))}
                        </LineChart>
                    ) : (
                        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                            <XAxis
                                dataKey="timestamp"
                                tick={{ fontSize: 11, fill: '#666' }}
                                axisLine={false}
                                tickLine={false}
                                minTickGap={30}
                                interval="preserveStartEnd"
                                tickFormatter={(value) => {
                                    try {
                                        const date = new Date(value);
                                        const now = new Date();
                                        const isToday = date.toDateString() === now.toDateString();
                                        if (isToday) {
                                            return date.toLocaleTimeString('zh-CN', {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            });
                                        } else {
                                            return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
                                        }
                                    } catch {
                                        return value;
                                    }
                                }}
                            />
                            <YAxis
                                tick={{ fontSize: 11, fill: '#666' }}
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
                                        const date = new Date(label);
                                        return date.toLocaleString('zh-CN');
                                    } catch {
                                        return label;
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
                            {activeModels.map((model) => (
                                <Line
                                    key={model.id}
                                    type="monotone"
                                    dataKey={model.id}
                                    name={model.name}
                                    stroke={model.color}
                                    strokeWidth={1.5}
                                    dot={false}
                                    isAnimationActive={false}
                                />
                            ))}
                        </LineChart>
                    )}
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ChartSection;

