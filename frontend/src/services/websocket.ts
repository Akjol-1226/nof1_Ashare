/**
 * WebSocket服务
 */

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8889';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private messageHandlers: Array<(data: any) => void> = [];
  private openHandlers: Array<() => void> = [];
  private closeHandlers: Array<() => void> = [];

  private refCount = 0;

  constructor(private endpoint: string) { }

  connect() {
    this.refCount++;
    console.log(`WebSocket connect requested. RefCount: ${this.refCount}`);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    if (this.refCount > 0 && !this.ws) {
      this.initConnection();
    }
  }

  private initConnection() {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}${this.endpoint}`);

      this.ws.onopen = () => {
        console.log(`WebSocket connected: ${this.endpoint}`);
        this.reconnectAttempts = 0;
        this.openHandlers.forEach((handler) => handler());
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageHandlers.forEach((handler) => handler(data));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.closeHandlers.forEach((handler) => handler());
        // 只有当还有引用者时才重连
        if (this.refCount > 0) {
          this.reconnect();
        } else {
          this.ws = null;
        }
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      if (this.refCount > 0) {
        this.reconnect();
      }
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => {
        if (this.refCount > 0) {
          this.initConnection();
        }
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }

  disconnect() {
    this.refCount--;
    console.log(`WebSocket disconnect requested. RefCount: ${this.refCount}`);

    if (this.refCount <= 0) {
      this.refCount = 0;
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
    }
  }

  onMessage(handler: (data: any) => void) {
    this.messageHandlers.push(handler);
  }

  offMessage(handler: (data: any) => void) {
    this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
  }

  onOpen(handler: () => void) {
    this.openHandlers.push(handler);
  }

  offOpen(handler: () => void) {
    this.openHandlers = this.openHandlers.filter(h => h !== handler);
  }

  onClose(handler: () => void) {
    this.closeHandlers.push(handler);
  }

  offClose(handler: () => void) {
    this.closeHandlers = this.closeHandlers.filter(h => h !== handler);
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

// 创建单例实例
// 创建单例实例
export const marketWebSocket = new WebSocketService('/ws/market');
export const tradingWebSocket = new WebSocketService('/ws/trading');
export const chatsWebSocket = new WebSocketService('/ws/chats');
export const performanceWebSocket = new WebSocketService('/ws/performance');
