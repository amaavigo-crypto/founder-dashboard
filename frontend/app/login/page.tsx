"use client";

import { useActionState } from "react";
import { login } from "@/lib/actions";

export default function LoginPage() {
  const [state, action, pending] = useActionState(login, undefined);
  return (
    <main className="login">
      <form action={action} className="card" style={{ padding: 28 }}>
        <div className="brand" style={{ padding: 0 }}><i /> Founders</div>
        <div><h1 style={{ fontSize: 22, margin: 0 }}>Sign in</h1><div className="eyebrow" style={{ marginTop: 4 }}>One place for every project.</div></div>
        <label>Email<input type="email" name="email" required autoComplete="username" /></label>
        <label>Password<input type="password" name="password" required autoComplete="current-password" /></label>
        {state?.error && <div className="err" role="alert">{state.error}</div>}
        <button className="btn" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</button>
      </form>
    </main>
  );
}
