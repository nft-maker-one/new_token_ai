import React, { useState, useEffect, useCallback } from 'react';
import TokenCard from './components/TokenCard';
import StatusBar from './components/StatusBar';
import { useWebSocket } from './hooks/useWebSocket';
import './App.css';

function App() {
  const [tokens, setTokens] = useState(new Map());
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [stats, setStats] = useState({
    totalTokens: 0,
    analyzingCount: 0,
    completedCount: 0
  });

  // 更新统计信息
  const updateStats = useCallback(() => {
    const tokenArray = Array.from(tokens.values());
    setStats({
      totalTokens: tokenArray.length,
      analyzingCount: tokenArray.filter(t => t.analysisStatus === 'ANALYZING').length,
      completedCount: tokenArray.filter(t => t.analysisStatus === 'COMPLETED').length
    });
  }, [tokens]);

  // WebSocket消息处理
  const handleMessage = useCallback((message) => {
    console.log('🎯 App收到WebSocket消息，开始处理...');

    try {
      const data = JSON.parse(message);
      console.log('🎯 App解析消息成功:', data.type);

      switch (data.type) {
        case 'new_token':
          console.log('🪙 App处理新代币:', data.data.symbol, data.data.name);
          console.log('🪙 代币数据:', data.data);

          setTokens(prev => {
            const newTokens = new Map(prev);
            const tokenData = {
              ...data.data,
              analysisStatus: 'PENDING',
              analysisProgress: 0,
              analysisResult: null
            };
            newTokens.set(data.data.mint, tokenData);
            console.log('🪙 代币已添加到状态，当前代币数量:', newTokens.size);
            return newTokens;
          });
          break;

        case 'analysis_update':
          console.log('🔄 App处理分析更新:', data.data.token_symbol, data.data.progress + '%');

          setTokens(prev => {
            const newTokens = new Map(prev);
            const token = newTokens.get(data.data.token_mint);
            if (token) {
              newTokens.set(data.data.token_mint, {
                ...token,
                analysisStatus: data.data.status,
                analysisProgress: data.data.progress,
                analysisResult: data.data
              });
              console.log('🔄 分析更新已应用到代币:', data.data.token_symbol);
            } else {
              console.warn('⚠️ 未找到要更新的代币:', data.data.token_mint);
            }
            return newTokens;
          });
          break;

        case 'analysis_complete':
          console.log('✅ App处理分析完成:', data.data.token_symbol);
          console.log("dissolve analysis_complete")
          setTokens(prev => {
            const newTokens = new Map(prev)
            const token = newTokens.get(data.data.token_mint)
            // if (token) {
              newTokens.set(data.data.token_mint, {
                // ...token,
              
                  mint:data.data.token_mint,
                  symbol:data.data.token_symbol,
                  name:data.data.token_name,
                  created_at:data.data.analysis_completed_at,
                  token_total_supply:100,
                  virtual_sol_reserves:100,
                  
                analysisStatus: 'COMPLETED',
                analysisProgress: 100,
                analysisResult: data.data
              })
              console.log('✅ 分析完成已应用到代币:', data.data.token_symbol);
            // } else {
            //   console.warn('⚠️ 未找到要完成分析的代币:', data.data.token_mint);
            // }
            return newTokens;
          })
          break;
        case 'analysis_complete_full':
          console.log('✅ App处理分析完成:', data.data.token_symbol);

          setTokens(prev => {
            const newTokens = new Map(prev);
            const token = newTokens.get(data.data.token_mint);
            if (token) {
              newTokens.set(data.data.token_mint, {
                ...token,
                analysisStatus: 'COMPLETED_FULL',
                analysisProgress: 100,
                analysisResult: data.data
              });
              console.log('✅ 分析完成已应用到代币:', data.data.token_symbol);
            } else {
              console.warn('⚠️ 未找到要完成分析的代币:', data.data.token_mint);
            }
            return newTokens;
          });
          break;

        default:
          console.log('❓ App收到未知消息类型:', data.type);
      }
    } catch (error) {
      console.error('❌ App解析WebSocket消息失败:', error);
      console.error('❌ 原始消息:', message);
    }
  }, []); // 移除所有依赖，直接在回调中处理状态

  // 使用WebSocket hook
  const { sendMessage } = useWebSocket('ws://localhost:8000/ws', {
    onMessage: handleMessage,
    onOpen: () => {
      console.log('🎯 App: WebSocket连接已打开');
      setConnectionStatus('connected');
    },
    onClose: () => {
      console.log('🎯 App: WebSocket连接已关闭');
      setConnectionStatus('disconnected');
    },
    onError: (error) => {
      console.error('🎯 App: WebSocket错误:', error);
      setConnectionStatus('error');
    }
  });



  // 监听tokens变化，更新统计信息
  useEffect(() => {
    console.log('🎯 App: tokens状态发生变化，当前代币数量:', tokens.size);
    console.log('🎯 App: 代币列表:', Array.from(tokens.keys()).map(key => {
      const token = tokens.get(key);
      return `${token.symbol}(${token.analysisStatus})`;
    }));
    updateStats();
  }, [tokens, updateStats]);

  // 监听连接状态变化
  useEffect(() => {
    console.log('🎯 App: 连接状态变化为:', connectionStatus);
  }, [connectionStatus]);

  // 监听统计信息变化
  useEffect(() => {
    console.log('🎯 App: 统计信息更新:', stats);
  }, [stats]);

  // 按时间排序代币（最新的在前）
  const sortedTokens = Array.from(tokens.values()).sort((a, b) => 
    new Date(b.created_at) - new Date(a.created_at)
  );

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>AI Crypto Token Analysis</h1>
          <p>实时代币监控与AI智能分析</p>
        </header>

        <StatusBar 
          connectionStatus={connectionStatus}
          stats={stats}
        />

        <main className="main-content">
          {sortedTokens.length === 0 ? (
            <div className="empty-state">
              <h3>等待新代币...</h3>
              <p>系统正在监控pump.fun上的新代币发行</p>
              <div className="loading-spinner"></div>
            </div>
          ) : (
            <div className="tokens-grid">
              {sortedTokens.map(token => (
                <TokenCard 
                  key={token.mint}
                  token={token}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
