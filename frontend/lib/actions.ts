"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { API_URL } from "./api";

export type FormState = { error?: string } | undefined;

export async function login(_: FormState, form: FormData): Promise<FormState> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      cache: "no-store",
    });
  } catch {
    return { error: "Can't reach the server. Try again in a moment." };
  }
  if (!res.ok) return { error: "Wrong email or password." };
  const { token } = await res.json();
  (await cookies()).set("fd_token", token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.COOKIE_SECURE !== "false" && process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  redirect("/");
}

export async function logout() {
  (await cookies()).delete("fd_token");
  redirect("/login");
}

export async function addProject(_: FormState, form: FormData): Promise<FormState> {
  const token = (await cookies()).get("fd_token")?.value;
  const clean = (k: string) => String(form.get(k) ?? "").trim() || null;
  const res = await fetch(`${API_URL}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      name: clean("name"),
      slug: clean("slug"),
      color: clean("color") ?? "#2F4BD0",
      base_url: clean("base_url"),
      api_key: clean("api_key"),
    }),
    cache: "no-store",
  });
  if (res.status === 401) redirect("/login");
  if (res.status === 409) return { error: "A project with this short name already exists." };
  if (!res.ok) return { error: "Check the fields. The short name must be lowercase letters, numbers and dashes." };
  const out = await res.json();
  if (out.first_pull_error) return { error: `Saved, but the first sync failed: ${out.first_pull_error}` };
  redirect(`/projects/${out.id}`);
}
