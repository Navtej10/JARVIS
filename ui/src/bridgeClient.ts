/**
 * bridgeClient.ts (V3+)
 *
 * WebSocket client for the Python <-> React bridge. Mirrors the schema
 * documented in bridge/websocket_server.py -- keep the two in sync.
 *
 * TODO(V3): implement connect() with auto-reconnect (the Python engine may
 *           start after the UI, or restart during development).
 * TODO(V3): implement sendRegisterObject() / sendUnregisterObject(), called
 *           by panels on mount/unmount/move (see panels/PanelBase.tsx).
 * TODO(V3): implement onGestureEvent() subscription used by panels/widgets
 *           to react to incoming gesture events targeting them.
 * TODO(V5): implement onAction() subscription for AI-planned actions.
 */

export type GestureEventMessage = {
  type: "gesture";
  name: string;
  state: "start" | "hold" | "release";
  target: string | null;
  screen_point: { x: number; y: number };
  timestamp_ms: number;
};

export type ActionMessage = {
  type: "action";
  target: string;
  intent: string;
  params: Record<string, unknown>;
};

export type BoundingBox = { x: number; y: number; width: number; height: number };

class BridgeClient {
  private socket: WebSocket | null = null;
  private gestureListeners: ((msg: GestureEventMessage) => void)[] = [];
  private actionListeners: ((msg: ActionMessage) => void)[] = [];
  
  private reconnectBackoff = 500;
  private messageQueue: string[] = [];
  private isConnecting = false;

  connect(url: string = "ws://localhost:8765"): void {
    if (this.socket?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }
    
    this.isConnecting = true;
    console.log(`Attempting to connect to bridge at ${url}...`);
    
    this.socket = new WebSocket(url);
    
    this.socket.onopen = () => {
      console.log("Connected to bridge server.");
      this.isConnecting = false;
      this.reconnectBackoff = 500; // reset backoff
      
      // Flush queued messages
      if (this.messageQueue.length > 0) {
        console.log(`Flushing ${this.messageQueue.length} queued messages...`);
        this.messageQueue.forEach(msg => this.socket?.send(msg));
        this.messageQueue = [];
      }
    };
    
    this.socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "gesture") {
          this.gestureListeners.forEach(listener => listener(msg));
        } else if (msg.type === "action") {
          this.actionListeners.forEach(listener => listener(msg));
        }
      } catch (err) {
        console.error("Failed to parse bridge message:", err);
      }
    };
    
    this.socket.onclose = () => {
      this.socket = null;
      this.isConnecting = false;
      console.log(`Bridge connection closed. Reconnecting in ${this.reconnectBackoff}ms...`);
      setTimeout(() => this.connect(url), this.reconnectBackoff);
      
      // Exponential backoff capped at 5000ms
      this.reconnectBackoff = Math.min(this.reconnectBackoff * 2, 5000);
    };
    
    this.socket.onerror = (err) => {
      // The onclose handler will take care of the reconnect
      console.error("Bridge connection error.", err);
    };
  }

  private sendOrQueue(payload: Record<string, unknown>) {
    const msg = JSON.stringify(payload);
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(msg);
    } else {
      this.messageQueue.push(msg);
    }
  }

  registerObject(id: string, kind: string, bounds: BoundingBox, zIndex: number): void {
    this.sendOrQueue({
      type: 'register_object',
      id,
      kind,
      bounds,
      z_index: zIndex
    });
  }

  unregisterObject(id: string): void {
    this.sendOrQueue({
      type: 'unregister_object',
      id
    });
  }

  onGestureEvent(listener: (msg: GestureEventMessage) => void): () => void {
    this.gestureListeners.push(listener);
    return () => {
      this.gestureListeners = this.gestureListeners.filter((l) => l !== listener);
    };
  }

  onAction(listener: (msg: ActionMessage) => void): () => void {
    this.actionListeners.push(listener);
    return () => {
      this.actionListeners = this.actionListeners.filter((l) => l !== listener);
    };
  }
}

export const bridgeClient = new BridgeClient();
