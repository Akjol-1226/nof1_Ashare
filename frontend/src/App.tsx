/**
 * 主应用组件
 */

import React, { useEffect } from 'react';
import { useAppStore } from './store';
import { apiService } from './services/api';
import { marketWebSocket } from './services/websocket';
import LeftPanel from './components/LeftPanel/LeftPanel';
import CenterPanel from './components/CenterPanel/CenterPanel';
import RightPanel from './components/RightPanel/RightPanel';
import './App.css';

function App() {
  const { setAIs, setRankings, setSystemStatus, setQuotes } = useAppStore();

  useEffect(() => {
    // 初始化数据
    loadInitialData();
    
    // 连接WebSocket
    marketWebSocket.connect();
    marketWebSocket.onMessage((data) => {
      if (data.type === 'market_update' && data.data) {
        setQuotes(data.data.quotes || []);
      }
    });
    
    // 定期刷新数据
    const interval = setInterval(() => {
      loadInitialData();
    }, 30000); // 每30秒刷新一次
    
    return () => {
      clearInterval(interval);
      marketWebSocket.disconnect();
    };
  }, []);

  const loadInitialData = async () => {
    try {
      // 并发加载数据
      const [ais, rankings, status] = await Promise.all([
        apiService.getAIList(),
        apiService.getAIRanking(),
        apiService.getSystemStatus(),
      ]);
      
      setAIs(ais);
      setRankings(rankings);
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>nof1.AShare</h1>
        <p>A股AI模拟交易竞赛</p>
      </header>
      
      <div className="app-layout">
        <LeftPanel />
        <CenterPanel />
        <RightPanel />
      </div>
    </div>
  );
}

export default App;
