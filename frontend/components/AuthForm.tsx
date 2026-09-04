"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

import { authenticate, AuthApiError } from "@/lib/auth-api";

const CONVERSATION_STORAGE_KEY = "sales_bot_conversation_id";

interface AuthFormProps {
  mode: "login" | "register";
}

interface FieldErrors {
  email?: string;
  displayName?: string;
  password?: string;
  confirmPassword?: string;
}

export default function AuthForm({ mode }: AuthFormProps) {
  const isRegister = mode === "register";
  const errorSummaryRef = useRef<HTMLDivElement>(null);
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (submitError) errorSummaryRef.current?.focus();
  }, [submitError]);

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!email.trim()) errors.email = "Enter your email address.";
    if (!password) errors.password = "Enter your password.";
    if (isRegister && password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }
    return errors;
  }

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const errors = validate();
    setFieldErrors(errors);
    setSubmitError(null);
    if (Object.keys(errors).length > 0) return;

    setIsSubmitting(true);
    try {
      await authenticate(
        mode,
        isRegister
          ? {
              email: email.trim(),
              display_name: displayName.trim(),
              password,
            }
          : { email: email.trim(), password },
      );
      window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
      window.location.assign("/");
    } catch (error) {
      if (error instanceof AuthApiError && error.status === 429) {
        setSubmitError(
          error.retryAfter
            ? `Too many attempts. Try again in ${error.retryAfter} seconds.`
            : "Too many attempts. Try again shortly.",
        );
      } else if (error instanceof Error) {
        setSubmitError(error.message);
      } else {
        setSubmitError("Authentication could not be completed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const fieldId = (name: string) => `auth-${name}`;
  const errorId = (name: string) => `${fieldId(name)}-error`;

  return (
    <form className="auth-form" onSubmit={submit} noValidate>
      {submitError ? (
        <div
          ref={errorSummaryRef}
          className="auth-form__summary"
          role="alert"
          tabIndex={-1}
        >
          {submitError}
        </div>
      ) : null}

      <div className="auth-form__intro">
        <p className="eyebrow">ChoTien account</p>
        <h1>{isRegister ? "Create your account" : "Welcome back"}</h1>
        <p>
          {isRegister
            ? "Save a clean starting point for your next phone search."
            : "Sign in to keep your conversations connected to your account."}
        </p>
      </div>

      <label className="auth-field" htmlFor={fieldId("email")}>
        <span>Email address</span>
        <input
          id={fieldId("email")}
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          aria-invalid={Boolean(fieldErrors.email)}
          aria-describedby={fieldErrors.email ? errorId("email") : undefined}
          maxLength={320}
        />
        {fieldErrors.email ? (
          <small id={errorId("email")}>{fieldErrors.email}</small>
        ) : null}
      </label>

      {isRegister ? (
        <label className="auth-field" htmlFor={fieldId("display-name")}>
          <span>Display name</span>
          <input
            id={fieldId("display-name")}
            name="display_name"
            type="text"
            autoComplete="name"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            aria-invalid={Boolean(fieldErrors.displayName)}
            aria-describedby={
              fieldErrors.displayName ? errorId("display-name") : undefined
            }
            maxLength={100}
          />
          {fieldErrors.displayName ? (
            <small id={errorId("display-name")}>{fieldErrors.displayName}</small>
          ) : null}
        </label>
      ) : null}

      <label className="auth-field" htmlFor={fieldId("password")}>
        <span>Password</span>
        <input
          id={fieldId("password")}
          name="password"
          type="password"
          autoComplete={isRegister ? "new-password" : "current-password"}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          aria-invalid={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? errorId("password") : undefined}
          minLength={12}
          maxLength={128}
        />
        {fieldErrors.password ? (
          <small id={errorId("password")}>{fieldErrors.password}</small>
        ) : null}
        {isRegister ? (
          <small className="auth-field__hint">Use 12–128 characters.</small>
        ) : null}
      </label>

      {isRegister ? (
        <label className="auth-field" htmlFor={fieldId("confirm-password")}>
          <span>Confirm password</span>
          <input
            id={fieldId("confirm-password")}
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            aria-invalid={Boolean(fieldErrors.confirmPassword)}
            aria-describedby={
              fieldErrors.confirmPassword ? errorId("confirm-password") : undefined
            }
            minLength={12}
            maxLength={128}
          />
          {fieldErrors.confirmPassword ? (
            <small id={errorId("confirm-password")}>
              {fieldErrors.confirmPassword}
            </small>
          ) : null}
        </label>
      ) : null}

      <button
        className="button button--primary auth-form__submit"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting
          ? isRegister
            ? "Creating account…"
            : "Signing in…"
          : isRegister
            ? "Register"
            : "Login"}
      </button>

      <p className="auth-form__switch">
        {isRegister ? "Already have an account?" : "New to ChoTien?"}{" "}
        <Link href={isRegister ? "/login" : "/register"}>
          {isRegister ? "Login" : "Register"}
        </Link>
      </p>
    </form>
  );
}
