import Link from "next/link";
import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import type { ProjectItem } from "@/lib/types";

export default async function ProjectsIndex() {
  const projects = await api<ProjectItem[]>("/api/projects");
  if (projects.length) redirect(`/projects/${projects[0].id}`);
  return (
    <main className="main">
      <div className="card empty">
        <h2 style={{ color: "var(--ink)", marginBottom: 8 }}>No projects yet</h2>
        <p>Connect your first product to see its numbers here.</p>
        <Link href="/projects/new">Add a project</Link>
      </div>
    </main>
  );
}
