"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getCurrentUser } from "@/lib/auth-api";
import type { AuthUser } from "@/lib/auth-types";

const CONVERSATION_STORAGE_KEY = "sales_bot_conversation_id";

export default function AuthStatus() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    getCurrentUser()
      .then((currentUser) => {
        if (isMounted) setUser(currentUser);
      })
      .catch(() => {
        if (isMounted) setError("Account status is temporarily unavailable.");
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function logout(): Promise<void> {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    setError(null);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
      window.location.assign("/");
    }
  }

  if (isLoading) {
    return <span className="auth-status__loading">Account</span>;
  }

  if (user) {
    return (
      <div className="auth-status">
        <span className="auth-status__identity" title={user.email}>
          {user.display_name || user.email}
        </span>
        <Link href="/account">Account</Link>
        <button type="button" onClick={logout} disabled={isLoggingOut}>
          {isLoggingOut ? "Logging out…" : "Logout"}
        </button>
      </div>
    );
  }

  return (
    <div className="auth-status">
      {error ? <span className="auth-status__error">{error}</span> : null}
      <Link href="/login">Login</Link>
      <Link className="auth-status__register" href="/register">
        Register
      </Link>
    </div>
  );
}
