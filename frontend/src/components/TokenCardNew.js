import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import moment from 'moment';

// 悬浮弹窗组件
const Tooltip = ({ children, content, title }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseEnter = (e) => {
    const rect = e.currentTarget.getBoundingClientRect(); //指向绑定事件的元素
    // e.target可能是子元素
    const newPosition = calculatePosition(rect);
    setPosition(newPosition);
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  // 计算tooltip位置，避免超出视口
  const calculatePosition = (triggerRect) => {
    const tooltipWidth = 300;
    const tooltipHeight = 50;
    const margin = 10;
     // 计算 tooltip 的初始 x 坐标（触发元素水平居中）
    let x = triggerRect.left + triggerRect.width / 2;
     // 计算 tooltip 的初始 y 坐标（触发元素上方）
    let y = triggerRect.top - tooltipHeight - margin;

    // 边界检测
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // 水平边界调整
    if (x - tooltipWidth / 2 < margin) {
      x = margin + tooltipWidth / 2;
    } else if (x + tooltipWidth / 2 > viewportWidth - margin) {
      x = viewportWidth - margin - tooltipWidth / 2;
    }

    // 垂直边界调整
    if (y < margin) {
      y = triggerRect.bottom + margin; // 显示在下方
    }

    return { x, y };
  };

  // 创建tooltip内容
  const tooltipContent = isVisible ? (
    <div
      className="tooltip-popup"
      style={{
        left: position.x,
        top: position.y,
        transform: 'translateX(-50%)',
        position: 'fixed',
        zIndex: 9999
      }}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      <div className="tooltip-header">{title}</div>
      <div className="tooltip-content">{content}</div>
    </div>
  ) : null;

  return (
    <div className="tooltip-container">
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="tooltip-trigger"
      >
        {children}
      </div>
      {/* 使用Portal将tooltip渲染到body，避免父容器限制 */}
      {isVisible && createPortal(tooltipContent, document.body)}
    </div>
  );
};

// 分析标签组件
const AnalysisTag = ({ type, tag, content, color = '#00d4ff' }) => {
  if (!tag && !content) return null;
  
  return (
    <Tooltip 
      title={type}
      content={content || '暂无详细分析'}
    >
      <div 
        className="analysis-tag"
        style={{ borderColor: color, color: color }}
      >
        <span className="tag-icon">●</span>
        <span className="tag-text">{tag || '分析中...'}</span>
      </div>
    </Tooltip>
  );
};

const TokenCard = ({ token }) => {
  const analysis = token.analysisResult;
  // console.log(analysis)
  const getStatusClass = (status) => {
    switch (status) {
      case 'PENDING': return 'status-pending';
      case 'ANALYZING': return 'status-analyzing';
      case 'COMPLETED': return 'status-completed';
      case 'FAILED': return 'status-failed';
      default: return 'status-pending';
    }
  };

  const getRiskLevel = (risk) => {
    if (typeof risk === 'string') {
      const riskLower = risk.toLowerCase();
      if (riskLower.includes('low')) return { level: 'LOW', color: '#28a745' };
      if (riskLower.includes('medium')) return { level: 'MED', color: '#ffc107' };
      if (riskLower.includes('high')) return { level: 'HIGH', color: '#ff6c00' };
      if (riskLower.includes('critical')) return { level: 'CRIT', color: '#dc3545' };
    }
    if (typeof risk === 'number') {
      if (risk <= 30) return { level: 'LOW', color: '#28a745' };
      if (risk <= 60) return { level: 'MED', color: '#ffc107' };
      if (risk <= 80) return { level: 'HIGH', color: '#ff6c00' };
      return { level: 'CRIT', color: '#dc3545' };
    }
    return { level: 'UNK', color: '#888' };
  };

  const formatNumber = (num) => {
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const formatTime = (timestamp) => {
    return moment(timestamp).format('HH:mm:ss');
  };

  const riskInfo = getRiskLevel(analysis?.risk_assessment);
  // console.log(token)
  return (
    <div className="token-card-compact">
      {/* 卡片头部 - 紧凑布局 */}
      <div className="token-header-compact">
        <div className="token-main-info">
          <div className="token-name-row">
            <h3 className="token-name">{token.name}</h3>
            <span className="token-symbol">{token.symbol}</span>
          </div>
          <div className="token-meta">
            <span className="token-time">{formatTime(token.created_at)}</span>
            <span className="token-supply">{formatNumber(token.token_total_supply)}</span>
          </div>
        </div>
        
        <div className="token-status-area">
          <div className={`token-status ${getStatusClass(analysis?.status || 'PENDING')}`}>
            {analysis?.status || 'PENDING'}
          </div>
          {analysis?.status === 'COMPLETED' && (
            <div 
              className="risk-badge"
              style={{ backgroundColor: riskInfo.color }}
            >
              {riskInfo.level}
            </div>
          )}
        </div>
      </div>

      {/* 进度条 */}
      {analysis?.progress !== undefined && (
        <div className="progress-bar-compact">
          <div 
            className="progress-fill"
            style={{ width: `${analysis.progress}%` }}
          />
        </div>
      )}

      {/* 分析标签区域 - 紧凑展示 */}
      {analysis?.status === 'COMPLETED' && (
        <div className="analysis-tags-grid">
          <AnalysisTag
            type="叙事分析"
            tag={analysis.narrative_tag || "叙事"}
            content={analysis.narrative_analysis}
            color="#00d4ff"
          />
          <AnalysisTag
            type="风险评估"
            tag={ `风险: ${riskInfo.level}`}
            content={`风险评分: ${analysis.risk_assessment}`}
            color={riskInfo.color}
          />
          <AnalysisTag
            type="市场分析"
            tag={analysis.market_tag || "市场"}
            content={analysis.market_analysis}
            color="#ff6b35"
          />
          <AnalysisTag
            type="AI总结"
            tag={analysis.ai_tag || "总结"}
            content={analysis.ai_summary}
            color="#9c27b0"
          />
          <AnalysisTag
            type="投资建议"
            tag={analysis.investment_tag || "建议"}
            content={analysis.investment_recommendation}
            color="#4caf50"
          />
        </div>
      )}

      {/* 代币数据概览 - 紧凑展示 */}
      <div className="token-data-compact">
        <div className="data-item">
          <span className="data-label">虚拟储备</span>
          <span className="data-value">{formatNumber(token.virtual_token_reserves)}</span>
        </div>
        <div className="data-item">
          <span className="data-label">SOL储备</span>
          <span className="data-value">{formatNumber(token.virtual_sol_reserves)}</span>
        </div>
        <div className="data-item">
          <span className="data-label">实际储备</span>
          <span className="data-value">{formatNumber(token.real_token_reserves)}</span>
        </div>
      </div>
    </div>
  );
};

export default TokenCard;
