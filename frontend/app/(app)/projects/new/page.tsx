"use client";

import { useActionState } from "react";
import { addProject } from "@/lib/actions";

export default function NewProject() {
  const [state, action, pending] = useActionState(addProject, undefined);
  return (
    <main className="main">
      <header className="head"><div><div className="eyebrow">Projects</div><h1>Add a project</h1></div></header>
      <form action={action} className="card formcard" style={{ maxWidth: 480 }}>
        <label>Name<input type="text" name="name" required maxLength={120} placeholder="HR Portal" /></label>
        <label>Short name<small>Lowercase letters, numbers and dashes. Used as its id.</small><input type="text" name="slug" required pattern="[a-z0-9][a-z0-9\-]{0,62}" placeholder="hr-portal" /></label>
        <label>Metrics URL<small>The product&apos;s /api/founder/metrics endpoint. Leave empty to enter money by hand.</small><input type="url" name="base_url" placeholder="https://hr.example.com/api/founder/metrics" /></label>
        <label>API key<small>Sent as a Bearer token. Stored on the server only.</small><input type="password" name="api_key" autoComplete="off" /></label>
        <label>Colour<input type="color" name="color" defaultValue="#2f4bd0" /></label>
        {state?.error && <div className="err" role="alert">{state.error}</div>}
        <button className="btn" disabled={pending}>{pending ? "Saving…" : "Add project"}</button>
      </form>
    </main>
  );
}
