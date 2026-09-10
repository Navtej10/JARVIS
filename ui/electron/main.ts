import { app, BrowserWindow, ipcMain } from 'electron';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

process.env.APP_ROOT = join(__dirname, '..');
export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL'];
export const MAIN_DIST = join(process.env.APP_ROOT, 'dist-electron');
export const RENDERER_DIST = join(process.env.APP_ROOT, 'dist');

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? join(process.env.APP_ROOT, 'public') : RENDERER_DIST;

let win: BrowserWindow | null;

function createWindow() {
  win = new BrowserWindow({
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    fullscreen: true,
    webPreferences: {
      preload: join(__dirname, 'preload.mjs'),
    },
  });

  // Make the entire window click-through initially
  win.setIgnoreMouseEvents(true, { forward: true });

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(join(RENDERER_DIST, 'index.html'));
  }
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
    win = null;
  }
});

app.on('ready', () => {
  createWindow();

  // Listen to IPC from the renderer to toggle click-through behavior
  ipcMain.on('set-ignore-mouse-events', (event, ignore) => {
    const webContents = event.sender;
    const currentWindow = BrowserWindow.fromWebContents(webContents);
    if (currentWindow) {
      currentWindow.setIgnoreMouseEvents(ignore, { forward: true });
    }
  });
});
