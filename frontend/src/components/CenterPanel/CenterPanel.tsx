/**
 * 中间面板 - 账户价值图表
 */

import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useAppStore } from '../../store';
import { apiService } from '../../services/api';
import './CenterPanel.css';

const CenterPanel: React.FC = () => {
  const { ais, rankings } = useAppStore();
  const [chartData, setChartData] = useState<any[]>([]);
  const [visibleAIs, setVisibleAIs] = useState<Set<number>>(new Set());

  useEffect(() => {
    // 初始化显示所有AI
    if (ais.length > 0) {
      setVisibleAIs(new Set(ais.map(ai => ai.id)));
    }
  }, [ais]);

  useEffect(() => {
    // 生成模拟图表数据（实际项目中应该从API获取历史数据）
    const generateChartData = () => {
      const data = [];
      const now = Date.now();
      const interval = 10000; // 10秒
      
      for (let i = 0; i < 50; i++) {
        const timestamp = new Date(now - (50 - i) * interval);
        const dataPoint: any = {
          time: timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          timestamp: timestamp.getTime()
        };
        
        // 为每个AI生成数据点
        rankings.forEach((ranking) => {
          // 模拟价格波动
          const baseValue = ranking.total_assets;
          const volatility = baseValue * 0.001; // 0.1%波动
          const randomChange = (Math.random() - 0.5) * volatility;
          dataPoint[`ai_${ranking.ai_id}`] = baseValue + randomChange;
        });
        
        data.push(dataPoint);
      }
      
      return data;
    };
    
    if (rankings.length > 0) {
      setChartData(generateChartData());
    }
  }, [rankings]);

  const toggleAI = (aiId: number) => {
    setVisibleAIs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(aiId)) {
        newSet.delete(aiId);
      } else {
        newSet.add(aiId);
      }
      return newSet;
    });
  };

  const colors = ['#667eea', '#f56565', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac'];

  return (
    <div className="center-panel">
      <div className="chart-header">
        <h2>总账户价值</h2>
        <div className="market-status">
          <span className="status-badge">实时行情</span>
        </div>
      </div>
      
      <div className="chart-container">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="time" 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                contentStyle={{ 
                  background: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.5rem'
                }}
                formatter={(value: number) => `¥${value.toFixed(2)}`}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
                onClick={(e) => {
                  const aiId = parseInt(e.value.replace('ai_', ''));
                  toggleAI(aiId);
                }}
              />
              {rankings.map((ranking, index) => (
                visibleAIs.has(ranking.ai_id) && (
                  <Line
                    key={ranking.ai_id}
                    type="monotone"
                    dataKey={`ai_${ranking.ai_id}`}
                    name={ranking.ai_name}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    dot={false}
                    animationDuration={300}
                  />
                )
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="chart-empty">
            <p>暂无数据</p>
            <p className="hint">请先注册AI并启动交易系统</p>
          </div>
        )}
      </div>
      
      <div className="chart-legend">
        {rankings.map((ranking, index) => (
          <div 
            key={ranking.ai_id} 
            className={`legend-item ${visibleAIs.has(ranking.ai_id) ? 'active' : 'inactive'}`}
            onClick={() => toggleAI(ranking.ai_id)}
          >
            <div 
              className="legend-color" 
              style={{ background: colors[index % colors.length] }}
            />
            <span className="legend-name">{ranking.ai_name}</span>
            <span className="legend-value">¥{ranking.total_assets.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CenterPanel;


