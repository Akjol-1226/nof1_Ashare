/**
 * 右侧面板 - 持仓、订单、决策日志
 */

import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store';
import { apiService } from '../../services/api';
import { Portfolio, Order, DecisionLog } from '../../types';
import './RightPanel.css';

type Tab = 'portfolio' | 'orders' | 'decisions';

const RightPanel: React.FC = () => {
  const { ais, rankings } = useAppStore();
  const [activeTab, setActiveTab] = useState<Tab>('portfolio');
  const [selectedAIIndex, setSelectedAIIndex] = useState(0);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [decisions, setDecisions] = useState<DecisionLog[]>([]);
  const [loading, setLoading] = useState(false);

  const selectedAI = rankings[selectedAIIndex];

  useEffect(() => {
    if (selectedAI) {
      loadData();
    }
  }, [selectedAI, activeTab]);

  const loadData = async () => {
    if (!selectedAI) return;
    
    setLoading(true);
    try {
      if (activeTab === 'portfolio') {
        const data = await apiService.getAIPortfolio(selectedAI.ai_id);
        setPortfolio(data);
      } else if (activeTab === 'orders') {
        const data = await apiService.getAIOrders(selectedAI.ai_id, 50);
        setOrders(data);
      } else if (activeTab === 'decisions') {
        const data = await apiService.getAIDecisions(selectedAI.ai_id, 50);
        setDecisions(data);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const nextAI = () => {
    setSelectedAIIndex((prev) => (prev + 1) % rankings.length);
  };

  const prevAI = () => {
    setSelectedAIIndex((prev) => (prev - 1 + rankings.length) % rankings.length);
  };

  return (
    <div className="right-panel">
      {/* 标签页导航 */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
          onClick={() => setActiveTab('portfolio')}
        >
          Portfolio
        </button>
        <button
          className={`tab ${activeTab === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveTab('orders')}
        >
          Orders
        </button>
        <button
          className={`tab ${activeTab === 'decisions' ? 'active' : ''}`}
          onClick={() => setActiveTab('decisions')}
        >
          Decision Log
        </button>
      </div>

      {/* AI选择器 */}
      {rankings.length > 0 && (
        <div className="ai-selector">
          <button className="nav-btn" onClick={prevAI} disabled={rankings.length <= 1}>
            ‹
          </button>
          <div className="ai-info">
            <div className="ai-avatar">
              {selectedAI?.ai_name.charAt(0).toUpperCase()}
            </div>
            <div className="ai-details">
              <div className="ai-name-text">{selectedAI?.ai_name}</div>
              <div className="ai-stats">
                <span>总资产: ¥{selectedAI?.total_assets.toFixed(2)}</span>
                <span className={selectedAI?.return_rate >= 0 ? 'positive' : 'negative'}>
                  {selectedAI?.return_rate >= 0 ? '+' : ''}{selectedAI?.return_rate.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
          <button className="nav-btn" onClick={nextAI} disabled={rankings.length <= 1}>
            ›
          </button>
        </div>
      )}

      {/* 内容区域 */}
      <div className="content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : rankings.length === 0 ? (
          <div className="empty-state">暂无AI参赛者</div>
        ) : (
          <>
            {activeTab === 'portfolio' && portfolio && (
              <div className="portfolio-view">
                <div className="summary">
                  <div className="summary-item">
                    <div className="label">现金</div>
                    <div className="value">¥{portfolio.cash.toFixed(2)}</div>
                  </div>
                  <div className="summary-item">
                    <div className="label">持仓市值</div>
                    <div className="value">
                      ¥{portfolio.positions.reduce((sum, p) => sum + p.market_value, 0).toFixed(2)}
                    </div>
                  </div>
                </div>
                
                <div className="positions-table">
                  {portfolio.positions.length > 0 ? (
                    <table>
                      <thead>
                        <tr>
                          <th>代码</th>
                          <th>持仓</th>
                          <th>盈亏</th>
                        </tr>
                      </thead>
                      <tbody>
                        {portfolio.positions.map((pos) => (
                          <tr key={pos.stock_code}>
                            <td>
                              <div>{pos.stock_code}</div>
                              <div className="stock-name">{pos.stock_name}</div>
                            </td>
                            <td>{pos.quantity}股</td>
                            <td className={pos.profit_loss_percent >= 0 ? 'positive' : 'negative'}>
                              {pos.profit_loss_percent >= 0 ? '+' : ''}{pos.profit_loss_percent.toFixed(2)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="empty-state">暂无持仓</div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'orders' && (
              <div className="orders-view">
                {orders.length > 0 ? (
                  <div className="orders-list">
                    {orders.map((order) => (
                      <div key={order.id} className="order-item">
                        <div className="order-header">
                          <span className={`direction ${order.direction}`}>
                            {order.direction === 'buy' ? '买入' : '卖出'}
                          </span>
                          <span className={`status ${order.status}`}>{order.status}</span>
                        </div>
                        <div className="order-body">
                          <div>{order.stock_code} {order.stock_name}</div>
                          <div>数量: {order.quantity}股</div>
                          {order.price && <div>价格: ¥{order.price.toFixed(2)}</div>}
                        </div>
                        <div className="order-time">
                          {new Date(order.created_at).toLocaleString('zh-CN')}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">暂无订单</div>
                )}
              </div>
            )}

            {activeTab === 'decisions' && (
              <div className="decisions-view">
                {decisions.length > 0 ? (
                  <div className="decisions-list">
                    {decisions.map((decision) => (
                      <div key={decision.id} className="decision-item">
                        <div className="decision-header">
                          <span className={`decision-type ${decision.decision}`}>
                            {decision.decision || 'N/A'}
                          </span>
                          <span className={decision.success ? 'success' : 'error'}>
                            {decision.success ? '✓' : '✗'}
                          </span>
                        </div>
                        {decision.stock_code && (
                          <div className="decision-action">
                            {decision.stock_code} × {decision.quantity}股
                          </div>
                        )}
                        {decision.reasoning && (
                          <div className="decision-reasoning">{decision.reasoning}</div>
                        )}
                        <div className="decision-time">
                          {new Date(decision.created_at).toLocaleString('zh-CN')} 
                          {' '}({decision.execution_time.toFixed(2)}s)
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">暂无决策记录</div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default RightPanel;


