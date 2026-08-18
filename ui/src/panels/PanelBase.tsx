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

export function PanelBase({ id, title, initialX, initialY, width, height, zIndex = 0, children }: PanelBaseProps) {
  const [position, setPosition] = useState({ x: initialX, y: initialY });
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // TODO(V3): bridgeClient.registerObject(id, "panel", {x: position.x, y: position.y, width, height}, zIndex)
    return () => {
      // TODO(V3): bridgeClient.unregisterObject(id)
    };
  }, [id, position, width, height, zIndex]);

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
