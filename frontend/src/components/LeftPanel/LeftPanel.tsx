/**
 * 左侧面板 - AI列表和系统控制
 */

import React, { useState } from 'react';
import { useAppStore } from '../../store';
import { apiService } from '../../services/api';
import './LeftPanel.css';

const LeftPanel: React.FC = () => {
  const { ais, rankings, systemStatus, setSystemStatus } = useAppStore();
  const [isStarting, setIsStarting] = useState(false);

  const handleStart = async () => {
    setIsStarting(true);
    try {
      const result = await apiService.startSystem();
      console.log(result.message);
      // 刷新状态
      const status = await apiService.getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to start system:', error);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStop = async () => {
    try {
      const result = await apiService.stopSystem();
      console.log(result.message);
      // 刷新状态
      const status = await apiService.getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to stop system:', error);
    }
  };

  return (
    <div className="left-panel">
      <div className="panel-title">AI Stock</div>
      
      <div className="ai-list">
        {rankings.map((ranking) => (
          <div key={ranking.ai_id} className="ai-item">
            <div className="ai-name">
              <span className={ranking.is_active ? 'status active' : 'status inactive'}>
                {ranking.is_active ? '✓' : '✗'}
              </span>
              {ranking.ai_name}
            </div>
            <div className={`ai-return ${ranking.return_rate >= 0 ? 'positive' : 'negative'}`}>
              {ranking.return_rate >= 0 ? '+' : ''}{ranking.return_rate.toFixed(2)}%
            </div>
            <div className="ai-assets">
              ¥{ranking.total_assets.toFixed(2)}
            </div>
          </div>
        ))}
        
        {rankings.length === 0 && (
          <div className="empty-state">暂无AI参赛者</div>
        )}
      </div>
      
      <div className="system-control">
        <div className="status-indicator">
          <span className={`indicator-dot ${systemStatus?.trading_time ? 'trading' : 'closed'}`} />
          {systemStatus?.trading_time ? '交易中' : '非交易时间'}
        </div>
        
        <div className="control-buttons">
          <button 
            className="btn btn-success" 
            onClick={handleStart}
            disabled={isStarting}
          >
            {isStarting ? '启动中...' : '启动交易'}
          </button>
          <button 
            className="btn btn-danger" 
            onClick={handleStop}
          >
            停止交易
          </button>
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;


