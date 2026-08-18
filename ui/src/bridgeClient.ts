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

  connect(url: string = "ws://localhost:8765"): void {
    throw new Error(
      "TODO(V3): open WebSocket to `url`, wire onmessage to dispatch to " +
        "gestureListeners/actionListeners based on message.type, and " +
        "auto-reconnect on close."
    );
  }

  registerObject(id: string, kind: string, bounds: BoundingBox, zIndex: number): void {
    throw new Error("TODO(V3): send {type: 'register_object', id, kind, bounds, z_index: zIndex}");
  }

  unregisterObject(id: string): void {
    throw new Error("TODO(V3): send {type: 'unregister_object', id}");
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
