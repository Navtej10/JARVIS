import React, { useEffect, useRef, useState } from "react";
import { bridgeClient } from "../bridgeClient";

/**
 * PanelBase.tsx (V3)
 *
 * Shared behavior for every floating spatial panel: registers its bounding
 * box with the Python ObjectManager on mount/move/unmount (via bridgeClient),
 * and listens for gesture events targeting it (pinch-select, grab-drag).
 *
 * Concrete panels (SystemPanel, ProjectsPanel, ...) wrap their content in
 * this component instead of reimplementing registration/drag logic each
 * time -- keeps every panel's grab/drag/select behavior consistent, which
 * matters for the "these 4 gestures should be extremely reliable and
 * uniform" philosophy carried over from V1.
 *
 * TODO(V3): on mount, call bridgeClient.registerObject(id, "panel", bounds, zIndex);
 *           on unmount, call bridgeClient.unregisterObject(id).
 * TODO(V3): subscribe via bridgeClient.onGestureEvent(), filter to events where
 *           event.target === id, and update local drag position state on
 *           "grab" hold/release events.
 * TODO(V3): re-register updated bounds whenever the panel moves (drag), so
 *           the Python-side hit-testing stays accurate.
 */
type PanelBaseProps = {
  id: string;
  title: string;
  initialX: number;
  initialY: number;
  width: number;
  height: number;
  zIndex?: number;
  children: React.ReactNode;
};

let globalZIndexCounter = 100;

export function PanelBase({ id, title, initialX, initialY, width, height, zIndex = 0, children }: PanelBaseProps) {
  const [position, setPosition] = useState({ x: initialX, y: initialY });
  const [panelZIndex, setPanelZIndex] = useState(zIndex || globalZIndexCounter++);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!panelRef.current) return;
    
    // Use actual rendered bounds rather than logical props to capture CSS exactness
    const rect = panelRef.current.getBoundingClientRect();
    
    bridgeClient.registerObject(
      id,
      "panel",
      {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      },
      panelZIndex
    );
    
    return () => {
      bridgeClient.unregisterObject(id);
    };
  }, [id, position, width, height, panelZIndex]);

  // Drag state for gesture handling
  const dragRef = useRef<{ cursor: { x: number; y: number }; pos: { x: number; y: number } } | null>(null);

  useEffect(() => {
    const unsubscribe = bridgeClient.onGestureEvent((msg) => {
      if (msg.target !== id) return;

      if (msg.name === "grab" && msg.screen_point) {
        if (msg.state === "start") {
          dragRef.current = { cursor: msg.screen_point, pos: position };
          setPanelZIndex(globalZIndexCounter++); // bring to front
        } else if (msg.state === "hold" && dragRef.current) {
          const dx = msg.screen_point.x - dragRef.current.cursor.x;
          const dy = msg.screen_point.y - dragRef.current.cursor.y;
          setPosition({
            x: dragRef.current.pos.x + dx,
            y: dragRef.current.pos.y + dy,
          });
        } else if (msg.state === "release") {
          dragRef.current = null;
        }
      } else if (msg.name === "pinch") {
        if (msg.state === "start") {
          console.log(`Panel pinched: ${id}`);
          setPanelZIndex(globalZIndexCounter++); // bring to front
        }
      }
    });

    return unsubscribe;
  }, [id, position]); // Depend on position so we get the latest when drag starts

  return (
    <div
      ref={panelRef}
      data-panel-id={id}
      style={{
        position: "absolute",
        left: position.x,
        top: position.y,
        width,
        height,
        zIndex: panelZIndex,
        pointerEvents: "auto",
        background: "rgba(20, 22, 30, 0.75)",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        borderRadius: 12,
        color: "#e6e6e6",
        fontFamily: "system-ui, sans-serif",
        backdropFilter: "blur(6px)",
      }}
    >
      <div style={{ padding: "8px 12px", fontSize: 12, letterSpacing: 1, opacity: 0.7, textTransform: "uppercase" }}>
        {title}
      </div>
      <div style={{ padding: "0 12px 12px" }}>{children}</div>
    </div>
  );
}
