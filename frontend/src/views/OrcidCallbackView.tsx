import { useEffect, useState } from "react";
import { ActionButton } from "../components/ui";
import type { View } from "../constants";

export function OrcidCallbackView({ onViewChange }: { onViewChange: (view: View, replace?: boolean) => void }) {
  const [message, setMessage] = useState("Completing ORCID sign in...");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const error = params.get("error");
    if (error) {
      setFailed(true);
      setMessage(error);
      return;
    }
    if (!token) {
      setFailed(true);
      setMessage("ORCID sign-in did not return an access token.");
      return;
    }
    sessionStorage.setItem("rom_access_token", token);
    localStorage.removeItem("rom_token");
    setMessage("Signed in with ORCID. Opening your workspace...");
    window.setTimeout(() => {
      onViewChange("dashboard", true);
      window.location.reload();
    }, 300);
  }, [onViewChange]);

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">ORCID OAuth 2.0</p>
          <h1>{failed ? "ORCID sign-in needs attention" : "Signing you in"}</h1>
          <p className={failed ? "alert error" : "muted"}>{message}</p>
        </div>
        {failed && (
          <ActionButton variant="primary" onClick={() => onViewChange("dashboard", true)}>
            Back to sign in
          </ActionButton>
        )}
      </section>
    </main>
  );
}
