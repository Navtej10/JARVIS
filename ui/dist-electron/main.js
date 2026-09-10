import { app, ipcMain, BrowserWindow } from "electron";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const __dirname$1 = dirname(fileURLToPath(import.meta.url));
process.env.APP_ROOT = join(__dirname$1, "..");
const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
const MAIN_DIST = join(process.env.APP_ROOT, "dist-electron");
const RENDERER_DIST = join(process.env.APP_ROOT, "dist");
process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? join(process.env.APP_ROOT, "public") : RENDERER_DIST;
let win;
function createWindow() {
  win = new BrowserWindow({
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    fullscreen: true,
    webPreferences: {
      preload: join(__dirname$1, "preload.mjs")
    }
  });
  win.setIgnoreMouseEvents(true, { forward: true });
  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(join(RENDERER_DIST, "index.html"));
  }
}
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
    win = null;
  }
});
app.on("ready", () => {
  createWindow();
  ipcMain.on("set-ignore-mouse-events", (event, ignore) => {
    const webContents = event.sender;
    const currentWindow = BrowserWindow.fromWebContents(webContents);
    if (currentWindow) {
      currentWindow.setIgnoreMouseEvents(ignore, { forward: true });
    }
  });
});
export {
  MAIN_DIST,
  RENDERER_DIST,
  VITE_DEV_SERVER_URL
};
