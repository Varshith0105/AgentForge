type MessageHandler = (data: Record<string, unknown>) => void;

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private channel: string;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 2000;     // start at 2 s
  private readonly MAX_DELAY = 60000; // cap at 60 s
  private reconnectAttempts = 0;
  private readonly MAX_ATTEMPTS = 8; // give up after 8 consecutive failures
  private enabled = true;

  public isConnected = false;

  constructor(channel = 'main') {
    this.channel = channel;
  }

  public connect(): void {
    if (!this.enabled) return;

    const token = localStorage.getItem('agentforge_token');
    if (!token) return;

    // Cancel any pending retry
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isLocalDev =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';
    const host = isLocalDev ? '127.0.0.1:8000' : window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/${this.channel}?token=${token}`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnected = true;
        this.reconnectDelay = 2000;
        this.reconnectAttempts = 0;
        console.log(`[WS] Connected to channel: ${this.channel}`);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Record<string, unknown>;
          const eventType = (data.type as string) || 'message';
          const handlers = this.handlers.get(eventType) || [];
          handlers.forEach((cb) => cb(data));
        } catch {
          // ignore malformed frames
        }
      };

      this.socket.onclose = (ev) => {
        this.isConnected = false;

        // 403 = auth failure — stop retrying (token is bad/expired)
        if (ev.code === 4003 || (ev.reason && ev.reason.includes('403'))) {
          console.warn('[WS] Auth failure — stopping reconnect.');
          return;
        }

        this.reconnectAttempts += 1;
        if (this.reconnectAttempts > this.MAX_ATTEMPTS) {
          console.warn(`[WS] Giving up after ${this.MAX_ATTEMPTS} retries.`);
          return;
        }

        console.log(
          `[WS] Closed (attempt ${this.reconnectAttempts}), retrying in ${this.reconnectDelay}ms…`,
        );
        this.reconnectTimer = setTimeout(() => this.connect(), this.reconnectDelay);
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.MAX_DELAY);
      };

      this.socket.onerror = () => {
        // onerror is always followed by onclose; let onclose handle retry logic
        this.isConnected = false;
      };
    } catch (e) {
      console.warn('[WS] Failed to initialise WebSocket:', e);
    }
  }

  public on(type: string, handler: MessageHandler): void {
    if (!this.handlers.has(type)) this.handlers.set(type, []);
    this.handlers.get(type)!.push(handler);
  }

  public send(data: unknown): boolean {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  public disconnect(): void {
    this.enabled = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  /** Re-enable after a logout/login cycle */
  public reconnect(): void {
    this.enabled = true;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 2000;
    this.connect();
  }
}

export const wsClient = new WebSocketClient('main');
