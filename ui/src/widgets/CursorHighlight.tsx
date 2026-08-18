import React from "react";

/**
 * CursorHighlight.tsx (V3)
 *
 * Subtle visual feedback for gesture recognition (the roadmap explicitly
 * calls out visual/audio feedback as necessary -- without it, users can't
 * tell if a gesture failed to register or is just slow, which kills trust
 * in the system fast).
 *
 * TODO(V3): subscribe to bridgeClient.onGestureEvent(); on "start"/"hold",
 *           render a soft glow at event.screen_point; on "release", fade out.
 * TODO(V3): optionally trigger a short audio click on successful pinch-select
 *           (see roadmap's V2 feedback note, applies equally to V3 panels).
 */
export function CursorHighlight() {
  throw new Error("TODO(V3): implement gesture visual feedback widget");
}
