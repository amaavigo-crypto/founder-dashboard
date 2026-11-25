import Link from "next/link";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";
import { logout } from "@/lib/actions";
import type { ProjectItem } from "@/lib/types";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const projects = await api<ProjectItem[]>("/api/projects");
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand"><i /> Founders</div>
        <Nav />
        <div className="side-projects">
          <div className="side-label">Your projects</div>
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`} className="side-proj">
              <span className="dot" style={{ background: p.color }} />
              {p.name}
            </Link>
          ))}
          <Link href="/projects/new" className="side-proj" style={{ color: "var(--muted)" }}>+ Add project</Link>
        </div>
        <div className="spacer" />
        <form action={logout}><button className="linkbtn" type="submit">Sign out</button></form>
      </aside>
      {children}
    </div>
  );
}
