import React, { useEffect, useState, useRef } from "react";
import { bridgeClient } from "../bridgeClient";

/**
 * CursorHighlight.tsx (V3)
 *
 * Subtle visual feedback for gesture recognition (the roadmap explicitly
 * calls out visual/audio feedback as necessary -- without it, users can't
 * tell if a gesture failed to register or is just slow, which kills trust
 * in the system fast).
 */
export function CursorHighlight() {
  const [point, setPoint] = useState<{ x: number; y: number } | null>(null);
  const [activeGesture, setActiveGesture] = useState<string | null>(null);
  const [isFading, setIsFading] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const unsubscribe = bridgeClient.onGestureEvent((msg) => {
      // Only show feedback for pinch and grab for now
      if (msg.name !== "pinch" && msg.name !== "grab") return;
      
      if (!msg.screen_point) return;

      if (msg.state === "start" || msg.state === "hold") {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
        
        setPoint(msg.screen_point);
        setActiveGesture(msg.name);
        setIsFading(false);
      } else if (msg.state === "release") {
        setIsFading(true);
        
        timeoutRef.current = setTimeout(() => {
          setActiveGesture(null);
          setPoint(null);
          setIsFading(false);
        }, 150); // Match CSS transition duration
      }
    });

    return unsubscribe;
  }, []);

  if (!point || !activeGesture) return null;

  const isPinch = activeGesture === "pinch";
  const radius = isPinch ? 20 : 50;
  
  // Bright blue tight glow for pinch, wider softer orange/red for grab
  const gradient = isPinch
    ? "radial-gradient(circle, rgba(100,200,255,0.8) 0%, rgba(100,200,255,0) 70%)"
    : "radial-gradient(circle, rgba(255,100,80,0.5) 0%, rgba(255,100,80,0) 70%)";

  return (
    <div
      style={{
        position: "absolute",
        left: point.x - radius,
        top: point.y - radius,
        width: radius * 2,
        height: radius * 2,
        background: gradient,
        borderRadius: "50%",
        pointerEvents: "none",
        zIndex: 9999,
        opacity: isFading ? 0 : 1,
        transition: "opacity 150ms ease-out",
      }}
    />
  );
}
