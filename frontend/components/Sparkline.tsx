export default function Sparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null;
  const mn = Math.min(...data), mx = Math.max(...data), n = data.length - 1;
  const pts = data.map((v, i) => `${((i * 88) / n).toFixed(1)},${(30 - ((v - mn) / (mx - mn || 1)) * 27).toFixed(1)}`).join(" ");
  return (
    <svg width="88" height="32" viewBox="0 0 88 32" aria-hidden="true">
      <polyline points={pts} fill="none" stroke="#2F4BD0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
