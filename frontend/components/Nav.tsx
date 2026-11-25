"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const icon = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;

const items = [
  { href: "/", label: "Overview", match: (p: string) => p === "/", svg: <svg {...icon}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg> },
  { href: "/projects", label: "Projects", match: (p: string) => p.startsWith("/projects"), svg: <svg {...icon}><path d="M3 7l9-4 9 4-9 4-9-4z" /><path d="M3 12l9 4 9-4" /><path d="M3 17l9 4 9-4" /></svg> },
  { href: "/money", label: "Money", match: (p: string) => p.startsWith("/money"), svg: <svg {...icon}><rect x="3" y="6" width="18" height="12" rx="2" /><circle cx="12" cy="12" r="2.5" /></svg> },
];

export default function Nav() {
  const path = usePathname();
  return (
    <nav className="nav" aria-label="Main">
      {items.map((i) => (
        <Link key={i.href} href={i.href} aria-current={i.match(path) ? "page" : undefined}>
          {i.svg}
          {i.label}
        </Link>
      ))}
    </nav>
  );
}
