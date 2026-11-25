import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export async function api<T>(path: string): Promise<T> {
  const token = (await cookies()).get("fd_token")?.value;
  const res = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: "no-store",
  });
  if (res.status === 401) redirect("/login");
  if (res.status === 404) throw new Error("not-found");
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

export function parseRange(r?: string): "7d" | "30d" | "90d" {
  return r === "7d" || r === "90d" ? r : "30d";
}
