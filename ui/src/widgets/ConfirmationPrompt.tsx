import React from "react";

/**
 * ConfirmationPrompt.tsx (V5)
 *
 * Brief visual confirm state shown before executing a destructive
 * AI-planned action (close, delete), per ai/planner.py's confirmation flow.
 *
 * TODO(V5): subscribe to bridgeClient.onAction(); when an action arrives
 *           with a destructive intent needing confirmation, render this
 *           prompt and wait for a confirming gesture/voice response before
 *           the Python side proceeds (round-trip confirmation over the
 *           bridge -- schema TBD alongside ai/planner.py).
 */
export function ConfirmationPrompt() {
  throw new Error("TODO(V5): implement destructive-action confirmation UI");
}
