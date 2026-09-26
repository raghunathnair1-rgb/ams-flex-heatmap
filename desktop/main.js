const { app, BrowserWindow, shell } = require("electron");

// Points at the live deployment by default, so the desktop app always shows
// the current app with no local server/backend to bundle or keep in sync.
// Override for local dev: ELECTRON_START_URL=http://localhost:5173 npm start
const START_URL = process.env.ELECTRON_START_URL || "https://ams-flex-heatmap.vercel.app";

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 720,
    minHeight: 560,
    title: "AMS Flex-Date Flight Finder",
    backgroundColor: "#0f1420",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  win.loadURL(START_URL);

  // Open any external link (e.g. Skyscanner/Google Flights compare links) in
  // the user's real browser instead of inside the app window.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
