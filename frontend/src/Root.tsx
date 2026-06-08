import { useState } from "react";
import { Landing } from "./Landing";
import App from "./App";

/** Top-level switch: marketing landing → real audit dashboard. */
export default function Root() {
  const [view, setView] = useState<"landing" | "app">("landing");
  const [seedUrl, setSeedUrl] = useState<string | undefined>();
  const [seedDomain, setSeedDomain] = useState<string | undefined>();

  if (view === "landing") {
    return (
      <Landing
        onAudit={(url) => {
          setSeedUrl(url);
          setSeedDomain(undefined);
          setView("app");
        }}
        onSample={() => {
          setSeedDomain("proplansolutions.io");
          setSeedUrl(undefined);
          setView("app");
        }}
      />
    );
  }
  return <App initialUrl={seedUrl} initialDomain={seedDomain} onHome={() => setView("landing")} />;
}
