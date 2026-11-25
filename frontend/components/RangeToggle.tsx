import Link from "next/link";

const OPTIONS = [["7d", "7 days"], ["30d", "30 days"], ["90d", "90 days"]] as const;

export default function RangeToggle({ current }: { current: string }) {
  return (
    <div className="seg" role="group" aria-label="Date range">
      {OPTIONS.map(([key, label]) => (
        <Link key={key} href={`?range=${key}`} aria-current={current === key} scroll={false}>
          {label}
        </Link>
      ))}
    </div>
  );
}
