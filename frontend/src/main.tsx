import React from "react";
import ReactDOM from "react-dom/client";
import { ChakraProvider, extendTheme } from "@chakra-ui/react";
import App from "./App";

const theme = extendTheme({
  styles: { global: { body: { bg: "gray.50" } } },
  fonts: {
    heading: `-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`,
    body: `-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`,
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </React.StrictMode>
);
