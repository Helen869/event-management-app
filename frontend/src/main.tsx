import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { NotificationProvider } from "./notifications";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <NotificationProvider>
      <App />
    </NotificationProvider>
  </StrictMode>,
);
