import React from 'react';

const StatusBar = ({ connectionStatus, stats }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return '#00ff00';
      case 'connecting':
        return '#ffff00';
      case 'disconnected':
      case 'error':
      default:
        return '#ff0000';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'connected':
        return '已连接';
      case 'connecting':
        return '连接中';
      case 'disconnected':
        return '已断开';
      case 'error':
        return '连接错误';
      default:
        return '未知状态';
    }
  };

  return (
    <div className="status-bar">
      <div className="status-item">
        <div 
          className={`status-dot ${connectionStatus !== 'connected' ? 'disconnected' : ''}`}
          style={{ backgroundColor: getStatusColor(connectionStatus) }}
        ></div>
        <span>连接状态: {getStatusText(connectionStatus)}</span>
      </div>
      
      <div className="status-item">
        <span>总代币数: {stats.totalTokens}</span>
      </div>
      
      <div className="status-item">
        <span>分析中: {stats.analyzingCount}</span>
      </div>
      
      <div className="status-item">
        <span>已完成: {stats.completedCount}</span>
      </div>
      
      <div className="status-item">
        <span>时间: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

export default StatusBar;
