"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const TOKEN_KEY = "pm-demo-token";

export const AuthGate = () => {
  const [user, setUser] = useState<string | null>(null);
  const [username, setUsername] = useState("user");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_KEY);

    if (!token) {
      setLoading(false);
      return;
    }

    fetch("/api/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("not authenticated");
        }

        const data = await response.json();
        setUser(data.user);
      })
      .catch(() => {
        window.localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error("Invalid credentials");
      }

      const data = await response.json();
      window.localStorage.setItem(TOKEN_KEY, data.token);
      setUser(data.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = async () => {
    const token = window.localStorage.getItem(TOKEN_KEY);

    if (token) {
      await fetch("/api/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    }

    window.localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setError(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] p-6 text-[var(--navy-dark)]">
        Checking session...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] p-6">
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-md rounded-[32px] border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)]"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            Sign in
          </p>
          <h1 className="mt-3 text-3xl font-semibold text-[var(--navy-dark)]">
            Open your board
          </h1>
          <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
            Use the demo credentials to continue to Kanban Studio.
          </p>

          <label className="mt-6 block text-sm font-medium text-[var(--navy-dark)]">
            Username
            <input
              className="mt-2 w-full rounded-2xl border border-[var(--stroke)] px-4 py-3 outline-none"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-[var(--navy-dark)]">
            Password
            <input
              type="password"
              className="mt-2 w-full rounded-2xl border border-[var(--stroke)] px-4 py-3 outline-none"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="mt-6 w-full rounded-full bg-[var(--primary-purple)] px-4 py-3 font-semibold text-white transition hover:opacity-90 disabled:opacity-70"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>

          <p className="mt-4 text-center text-sm text-[var(--gray-text)]">
            Demo credentials: user / password
          </p>
        </form>
      </div>
    );
  }

  return (
    <div>
      <div className="mx-auto flex max-w-[1500px] justify-end px-6 pt-4">
        <button
          onClick={handleLogout}
          className="rounded-full border border-[var(--stroke)] bg-white/80 px-4 py-2 text-sm font-semibold text-[var(--navy-dark)]"
        >
          Log out
        </button>
      </div>
      <KanbanBoard />
    </div>
  );
};
