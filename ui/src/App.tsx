import React from "react";
import { SystemPanel } from "./panels/SystemPanel";
import { ProjectsPanel } from "./panels/ProjectsPanel";
import { Scene3D } from "./three/Scene3D";

/**
 * App.tsx (V3+)
 *
 * Root of the spatial UI overlay. Renders floating 2D panels (V3) plus the
 * Three.js canvas for 3D object manipulation (V4). This sits in a
 * transparent, click-through-where-empty, always-on-top window above the
 * real desktop -- see index.html and the OS-level overlay window setup
 * (outside this scaffold's scope; typically an Electron/native shell).
 *
 * TODO(V3): call bridgeClient.connect() once on mount (e.g. in a useEffect
 *           here or in a small provider component).
 * TODO(V4): only mount <Scene3D /> once there are 3D objects to manipulate --
 *           keep it absent/inert during V3 panel-only work.
 */
export default function App() {
  return (
    <div style={{ width: "100vw", height: "100vh", pointerEvents: "none" }}>
      <SystemPanel />
      <ProjectsPanel />
      {/* TODO(V4): <Scene3D /> */}
    </div>
  );
}
