import React from "react";
import { Canvas } from "@react-three/fiber";

/**
 * Scene3D.tsx (V4)
 *
 * Three.js canvas (via @react-three/fiber) for 3D object manipulation:
 * two-hand scale, pinch+rotate, orbit. Objects rendered here are the same
 * "SpatialObject" kind registered with the Python ObjectManager (kind:
 * "3d_object"), so gesture targeting works uniformly across 2D panels and
 * 3D objects.
 *
 * TODO(V4): render manipulable objects driven by state synced from the
 *           bridge (position/rotation/scale updated on incoming gesture
 *           events, e.g. TwoHandScaleGesture / RotateGesture from
 *           gestures/rotate.py).
 * TODO(V4): use Three.js's standard transform-gizmo patterns for
 *           rotate/scale rather than inventing custom 3D math, per the
 *           roadmap's guidance.
 */
export function Scene3D() {
  return (
    <Canvas style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {/* TODO(V4): lighting, camera, and manipulable mesh objects go here */}
    </Canvas>
  );
}
