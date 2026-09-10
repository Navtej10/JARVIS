import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

declare global {
  interface Window {
    electronAPI?: {
      setIgnoreMouseEvents: (ignore: boolean) => void;
    };
  }
}

// Global mousemove listener to toggle click-through behavior in the Electron shell
window.addEventListener("mousemove", (e) => {
  if (window.electronAPI) {
    const isOverPanel = (e.target as Element)?.closest("[data-panel-id]");
    window.electronAPI.setIgnoreMouseEvents(!isOverPanel);
  }
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
