import React from "react";
import { PanelBase } from "./PanelBase";

/**
 * ProjectsPanel.tsx (V3)
 *
 * Example spatial panel from the roadmap's mockup: a list of projects the
 * user can point-and-pinch to select/open.
 *
 * TODO(V3): make each project row itself a registered SpatialObject (so
 *           hit-testing resolves to "project:InterviewAI" not just
 *           "projects-panel"), and wire pinch-select to trigger an
 *           interaction/action_executor.Action with intent="open".
 */
export function ProjectsPanel() {
  const projects = ["InterviewAI", "Expantra", "TimeLeap"];

  return (
    <PanelBase id="projects-panel" title="Projects" initialX={40} initialY={180} width={220} height={140} zIndex={1}>
      {projects.map((name) => (
        <div key={name} style={{ padding: "6px 0", fontSize: 14 }}>
          {name}
        </div>
      ))}
    </PanelBase>
  );
}
