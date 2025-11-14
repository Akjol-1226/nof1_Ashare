/**
 * API服务
 */

import { AI, Portfolio, Order, Transaction, DecisionLog, Quote, AIRanking, SystemStatus } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8888';

class APIService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // AI相关
  async getAIList(): Promise<AI[]> {
    return this.request<AI[]>('/api/ai/list');
  }

  async getAIPortfolio(aiId: number): Promise<Portfolio> {
    return this.request<Portfolio>(`/api/ai/${aiId}/portfolio`);
  }

  async getAIOrders(aiId: number, limit: number = 100): Promise<Order[]> {
    return this.request<Order[]>(`/api/ai/${aiId}/orders?limit=${limit}`);
  }

  async getAITransactions(aiId: number, limit: number = 100): Promise<Transaction[]> {
    return this.request<Transaction[]>(`/api/ai/${aiId}/transactions?limit=${limit}`);
  }

  async getAIDecisions(aiId: number, limit: number = 100): Promise<DecisionLog[]> {
    return this.request<DecisionLog[]>(`/api/ai/${aiId}/decisions?limit=${limit}`);
  }

  async getAIRanking(): Promise<AIRanking[]> {
    return this.request<AIRanking[]>('/api/ai/ranking');
  }

  async registerAI(data: {
    name: string;
    model_name: string;
    api_key?: string;
    base_url?: string;
    initial_cash?: number;
  }): Promise<AI> {
    return this.request<AI>('/api/ai/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // 市场数据
  async getMarketQuotes(limit: number = 50): Promise<{ timestamp: string; quotes: Quote[] }> {
    return this.request(`/api/market/quotes?limit=${limit}`);
  }

  async getStockList(): Promise<{ total: number; stocks: Array<{ code: string; name: string }> }> {
    return this.request('/api/market/stocks');
  }

  // 系统控制
  async getSystemStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/api/system/status');
  }

  async startSystem(): Promise<{ status: string; message: string }> {
    return this.request('/api/system/start', { method: 'POST' });
  }

  async stopSystem(): Promise<{ status: string; message: string }> {
    return this.request('/api/system/stop', { method: 'POST' });
  }
}

export const apiService = new APIService();
