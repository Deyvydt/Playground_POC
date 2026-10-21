import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { SessionProvider } from "./context/SessionContext.jsx";
import { UIProvider } from "./context/UIContext.jsx";
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "@fontsource/instrument-serif/400.css";
import "@fontsource/instrument-serif/400-italic.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <SessionProvider>
        <UIProvider>
          <App />
        </UIProvider>
      </SessionProvider>
    </BrowserRouter>
  </React.StrictMode>
);
