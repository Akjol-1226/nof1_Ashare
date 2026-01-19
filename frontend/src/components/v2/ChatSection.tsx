import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, Radio } from 'lucide-react';
import { AI_MODELS } from './constants';
import { ChatMessage, Theme } from './types';
import { chatsWebSocket } from '@/services/websocket';

interface Props {
    theme: Theme;
}

const ChatSection: React.FC<Props> = ({ theme }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);
    const isPop = theme === 'pop';

    useEffect(() => {
        // Connect to WebSocket
        chatsWebSocket.connect();

        // Listen for updates
        chatsWebSocket.onMessage((message) => {
            if (message.type === 'chats_update') {
                const data = message.data;
                if (data && data.chats) {
                    const allChats: ChatMessage[] = [];

                    data.chats.forEach((aiChat: any) => {
                        if (aiChat.chats) {
                            aiChat.chats.forEach((chat: any) => {
                                // Try to map AI name to our visual models
                                let modelId = 'default';
                                const nameLower = aiChat.ai_name.toLowerCase();
                                if (nameLower.includes('qwen')) modelId = 'qwen';
                                else if (nameLower.includes('deepseek')) modelId = 'deepseek';
                                else if (nameLower.includes('kimi')) modelId = 'kimi';
                                else if (nameLower.includes('gpt')) modelId = 'gpt4';
                                else if (nameLower.includes('claude')) modelId = 'claude';

                                allChats.push({
                                    id: `${aiChat.ai_name}-${chat.timestamp}`, // Generate a pseudo ID
                                    modelId: modelId,
                                    text: chat.reasoning,
                                    timestamp: new Date(chat.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
                                });
                            });
                        }
                    });

                    // Sort by timestamp desc for chat flow (newest top)
                    // Classic version shows newest top
                    allChats.sort((a, b) => b.timestamp.localeCompare(a.timestamp));

                    setMessages(allChats);
                }
            }
        });

        return () => {
            // chatsWebSocket.disconnect(); // Optional
        };
    }, []);

    // Remove auto-scroll for Glass theme to match Classic behavior

    const getModel = (id: string) => {
        const found = AI_MODELS.find(m => m.id === id);
        if (found) return found;
        // Fallback for unknown models
        return {
            id: id,
            name: id.toUpperCase(),
            avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${id}`,
            color: '#888888',
            description: 'AI Model'
        } as any;
    };

    return (
        <div className={`flex flex-col h-full relative ${isPop ? 'bg-secondary border-4 border-black shadow-hard' : 'glass-panel rounded-3xl shadow-glass'}`}>

            {/* Header */}
            <div className={`flex items-center justify-between ${isPop ? 'p-4 border-b-4 border-black bg-white' : 'p-6 border-b border-white/40 bg-white/30 backdrop-blur-md rounded-t-3xl'}`}>
                <div className="flex items-center space-x-3">
                    {isPop ? (
                        <h2 className="text-xl font-black text-black uppercase transform -skew-x-12">💬 AI 思考实况</h2>
                    ) : (
                        <div className="flex flex-col">
                            <h2 className="text-lg font-glassHeader font-bold text-slate-800">Strategy Stream</h2>
                            <span className="text-xs text-slate-500 font-glass">Live Reasoning Feed</span>
                        </div>
                    )}
                </div>

                {isPop ? (
                    <div className="px-3 py-1 bg-red-500 border-2 border-black text-white text-xs font-bold animate-pulse">LIVE</div>
                ) : (
                    <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-50/50 border border-emerald-100 text-emerald-600">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span className="text-[10px] font-bold tracking-wider">LIVE</span>
                    </div>
                )}
            </div>

            {/* Messages */}
            <div ref={scrollRef} className={`flex-1 overflow-y-auto ${isPop ? 'p-4 space-y-4 bg-secondary/20' : 'p-6 space-y-6'}`}>
                {messages.map((msg, idx) => {
                    const model = getModel(msg.modelId);

                    if (isPop) {
                        return (
                            <div key={idx} className="flex items-start space-x-3 group">
                                <div className="flex-shrink-0 -mt-2 relative z-10">
                                    <img
                                        src={model.avatar}
                                        alt={model.name}
                                        className="w-12 h-12 border-2 border-black bg-white rounded-none shadow-hard-sm"
                                    />
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-baseline mb-1">
                                        <span className="text-sm font-black text-black mr-2 bg-white border border-black px-1 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                                            {model.name}
                                        </span>
                                        <span className="text-xs text-gray-600 font-mono">{msg.timestamp}</span>
                                    </div>
                                    <div className="bg-white border-2 border-black p-3 shadow-hard text-sm font-medium leading-relaxed relative">
                                        <div className="absolute top-0 left-[-8px] w-0 h-0 border-t-[10px] border-t-black border-l-[10px] border-l-transparent"></div>
                                        <div className="absolute top-[3px] left-[-4px] w-0 h-0 border-t-[6px] border-t-white border-l-[6px] border-l-transparent"></div>
                                        {msg.text}
                                    </div>
                                </div>
                            </div>
                        );
                    } else {
                        // Glass Theme Message
                        return (
                            <div key={idx} className="flex items-start space-x-4">
                                <div className="relative">
                                    <img src={model.avatar} className="w-10 h-10 rounded-xl shadow-sm bg-white" />
                                    <div className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white" style={{ backgroundColor: model.color }}></div>
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center justify-between mb-1.5">
                                        <span className="text-sm font-glassHeader font-bold text-slate-800">{model.name}</span>
                                        <span className="text-[10px] font-mono text-slate-400">{msg.timestamp}</span>
                                    </div>
                                    <div className="p-4 bg-white/60 rounded-2xl rounded-tl-sm border border-white/60 shadow-sm text-slate-600 text-sm font-glass leading-relaxed hover:bg-white/80 transition-colors">
                                        {msg.text}
                                    </div>
                                </div>
                            </div>
                        );
                    }
                })}
                {messages.length === 0 && (
                    <div className="flex h-full items-center justify-center opacity-50 font-mono text-sm">Waiting for insights...</div>
                )}
            </div>
        </div>
    );
};

export default ChatSection;
