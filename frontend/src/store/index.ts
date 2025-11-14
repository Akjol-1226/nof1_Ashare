/**
 * Zustand状态管理
 */

import { create } from 'zustand';
import { AI, Portfolio, Quote, AIRanking, SystemStatus } from '../types';

interface AppState {
  // AI数据
  ais: AI[];
  selectedAI: AI | null;
  rankings: AIRanking[];
  
  // 持仓数据
  portfolios: Record<number, Portfolio>;
  
  // 市场数据
  quotes: Quote[];
  
  // 系统状态
  systemStatus: SystemStatus | null;
  
  // 操作
  setAIs: (ais: AI[]) => void;
  setSelectedAI: (ai: AI | null) => void;
  setRankings: (rankings: AIRanking[]) => void;
  setPortfolio: (aiId: number, portfolio: Portfolio) => void;
  setQuotes: (quotes: Quote[]) => void;
  setSystemStatus: (status: SystemStatus) => void;
}

export const useAppStore = create<AppState>((set) => ({
  ais: [],
  selectedAI: null,
  rankings: [],
  portfolios: {},
  quotes: [],
  systemStatus: null,
  
  setAIs: (ais) => set({ ais }),
  setSelectedAI: (ai) => set({ selectedAI: ai }),
  setRankings: (rankings) => set({ rankings }),
  setPortfolio: (aiId, portfolio) => 
    set((state) => ({
      portfolios: { ...state.portfolios, [aiId]: portfolio }
    })),
  setQuotes: (quotes) => set({ quotes }),
  setSystemStatus: (status) => set({ systemStatus: status }),
}));


