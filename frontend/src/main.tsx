import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import { ThemeProvider } from "./components/theme-provider";
import "./index.css";

// Service worker is automatically registered by vite-plugin-pwa

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider defaultTheme="light" storageKey="verse-ui-theme">
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);
