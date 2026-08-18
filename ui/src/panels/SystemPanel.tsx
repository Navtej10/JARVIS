import React from "react";
import { PanelBase } from "./PanelBase";

/**
 * SystemPanel.tsx (V3)
 *
 * Example spatial panel from the roadmap's mockup: shows live CPU/RAM.
 * Data source TODO -- either poll a small local stats endpoint from the
 * Python engine, or fetch directly in the browser via a native bridge,
 * depending on the eventual overlay-shell choice (Electron vs. browser).
 *
 * TODO(V3): wire real CPU/RAM values (e.g. Python engine exposes them over
 *           the same WebSocket bridge as a periodic "stats" message type).
 */
export function SystemPanel() {
  return (
    <PanelBase id="system-panel" title="System" initialX={40} initialY={40} width={220} height={100} zIndex={1}>
      <div>CPU: -- %</div>
      <div>RAM: -- %</div>
    </PanelBase>
  );
}
