import { useEffect, useState } from "react";
import { api } from "../api";
import type { View } from "../constants";

export function VerifyEmailView({ onViewChange }: { onViewChange: (view: View) => void }) {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") ?? "";
    if (!token) {
      setStatus("error");
      setMessage("Verification token is missing.");
      return;
    }
    api
      .verifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage("Email verified. You can sign in now.");
      })
      .catch((error) => {
        setStatus("error");
        setMessage((error as Error).message);
      });
  }, []);

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Research Opportunity Matcher</p>
          <h1>Email verification</h1>
          <p className="muted">{message}</p>
        </div>
        {status === "loading" && <span className="spinner" aria-hidden="true" />}
        {status === "success" && (
          <button className="primary" type="button" onClick={() => onViewChange("feed")}>
            Continue to sign in
          </button>
        )}
        {status === "error" && (
          <button className="secondary" type="button" onClick={() => onViewChange("feed")}>
            Back to sign in
          </button>
        )}
      </section>
    </main>
  );
}
