import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import {WritePolicyProvider} from "./lib/write-policy";
import "./styles.css";
import "./assurance-layout.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WritePolicyProvider><App /></WritePolicyProvider>
  </StrictMode>,
);
