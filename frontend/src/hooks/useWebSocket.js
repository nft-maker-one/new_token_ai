import { useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10
  } = options;

  const ws = useRef(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutId = useRef(null);
  const heartbeatIntervalId = useRef(null);
  const isManualClose = useRef(false);

  const connect = useCallback(() => {
    try {
      // 防止重复连接
      if (ws.current && ws.current.readyState === WebSocket.CONNECTING) {
        console.log('WebSocket正在连接中，跳过重复连接');
        return;
      }

      // 清理之前的连接
      if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
        ws.current.close();
      }

      console.log('创建新的WebSocket连接...');
      ws.current = new WebSocket(url);

      ws.current.onopen = (event) => {
        console.log('🔗 WebSocket连接成功建立');
        console.log('🔗 连接URL:', url);
        console.log('🔗 连接状态:', ws.current.readyState);
        reconnectAttempts.current = 0;
        isManualClose.current = false;

        // 启动心跳
        heartbeatIntervalId.current = setInterval(() => {
          if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            console.log('💓 发送心跳到服务器');
            ws.current.send('heartbeat');
          }
        }, 30000); // 每30秒发送一次心跳

        if (onOpen) onOpen(event);
      };

      ws.current.onmessage = (event) => {
        console.log('📥 收到WebSocket消息:', event.data);

        try {
          const data = JSON.parse(event.data);
          console.log('📥 解析后的消息:', data);

          if (data.type === 'heartbeat_response') {
            console.log('💓 收到心跳响应');
            return;
          }
          if (data.type === 'heartbeat') {
            console.log('💓 收到服务器心跳，发送响应');
            ws.current.send('heartbeat');
            return;
          }
          if (data.type === 'connection_status' && data.data.status === 'connected') {
            console.log('✅ 服务器确认WebSocket连接已建立');
            return;
          }
          if (data.type === 'new_token') {
            console.log('🪙 收到新代币消息:', data.data.symbol, data.data.name);
          }
          if (data.type === 'analysis_update') {
            console.log('🔄 收到分析更新:', data.data.token_symbol, data.data.progress + '%');
          }
          if (data.type === 'analysis_complete') {
            console.log('✅ 收到分析完成:', data.data.token_symbol);
          }
        } catch (e) {
          // 不是JSON格式的消息，可能是简单的pong响应
          if (event.data === 'pong') {
            console.log('🏓 收到pong响应');
            return;
          }
          console.log('📥 收到非JSON消息:', event.data);
        }

        console.log('📨 传递消息给应用处理器');
        if (onMessage) onMessage(event.data);
      };

      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket连接断开');
        console.log('🔌 断开代码:', event.code);
        console.log('🔌 断开原因:', event.reason);
        console.log('🔌 是否手动关闭:', isManualClose.current);

        // 清理心跳
        if (heartbeatIntervalId.current) {
          clearInterval(heartbeatIntervalId.current);
          heartbeatIntervalId.current = null;
          console.log('💓 心跳定时器已清理');
        }

        if (onClose) onClose(event);

        // 只有在非手动关闭且非正常关闭时才重连
        if (!isManualClose.current && event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectTimeoutId.current = setTimeout(() => {
            reconnectAttempts.current++;
            console.log(`🔄 尝试重新连接... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
            connect();
          }, reconnectInterval);
        } else if (event.code === 1000) {
          console.log('✅ WebSocket正常关闭');
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.log('❌ 已达到最大重连次数');
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      if (onError) onError(error);
    }
  }, [url]); // 只依赖URL，避免因为回调函数变化导致重连

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(message);
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    isManualClose.current = true;

    if (reconnectTimeoutId.current) {
      clearTimeout(reconnectTimeoutId.current);
      reconnectTimeoutId.current = null;
    }

    if (heartbeatIntervalId.current) {
      clearInterval(heartbeatIntervalId.current);
      heartbeatIntervalId.current = null;
    }

    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [url]); // 只依赖URL，避免无限重连

  return {
    sendMessage,
    disconnect,
    readyState: ws.current?.readyState
  };
};
