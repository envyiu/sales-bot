"use client";

import { useEffect, useState } from "react";

import { getCurrentUser } from "@/lib/auth-api";
import type { AuthUser } from "@/lib/auth-types";

const CONVERSATION_STORAGE_KEY = "sales_bot_conversation_id";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function AccountPanel() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then((currentUser) => {
        if (!currentUser) {
          window.location.assign("/login?next=/account");
          return;
        }
        setUser(currentUser);
      })
      .catch(() => setError("Could not load your account right now."))
      .finally(() => setIsLoading(false));
  }, []);

  async function logout(): Promise<void> {
    setIsLoggingOut(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
      window.location.assign("/");
    }
  }

  if (isLoading) {
    return <p className="account-panel__status">Loading account…</p>;
  }
  if (error) {
    return <p className="account-panel__error" role="alert">{error}</p>;
  }
  if (!user) return null;

  return (
    <section className="account-panel" aria-labelledby="account-title">
      <div className="account-panel__intro">
        <p className="eyebrow">Your account</p>
        <h1 id="account-title">{user.display_name || user.email}</h1>
        <p>One secure place for your ChoTien profile and chat sessions.</p>
      </div>
      <dl className="account-details">
        <div>
          <dt>Email</dt>
          <dd>{user.email}</dd>
        </div>
        <div>
          <dt>Display name</dt>
          <dd>{user.display_name || "Not set"}</dd>
        </div>
        <div>
          <dt>Member since</dt>
          <dd>{formatDate(user.created_at)}</dd>
        </div>
        <div>
          <dt>Current session ends</dt>
          <dd>{formatDate(user.session_expires_at)}</dd>
        </div>
      </dl>
      <button className="button account-panel__logout" type="button" onClick={logout} disabled={isLoggingOut}>
        {isLoggingOut ? "Logging out…" : "Logout"}
      </button>
    </section>
  );
}
