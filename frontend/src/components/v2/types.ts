export interface Stock {
    symbol: string;
    name: string;
    price: number;
    change: number; // Percentage
    shares: number;
    available: number;
    avgCost: number;
    profit: number; // Absolute profit value
}

export interface AiModel {
    id: string;
    name: string;
    avatar: string;
    color: string;
    totalValue: number;
    totalProfit: number; // Total profit/loss amount
    pnlPercent: number;
    holdings: Stock[];
    description: string;
}

export interface ChatMessage {
    id: string;
    modelId: string;
    text: string;
    timestamp: string;
}

export interface ChartDataPoint {
    time: string;
    [key: string]: number | string;
}

export interface TickerItem {
    name: string;
    price: number;
    change: number;
}

export type Theme = 'pop' | 'glass';
