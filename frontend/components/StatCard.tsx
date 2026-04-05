interface StatCardProps {
  label: string
  value: string | number
  sub?: string
}

export function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div className="bg-surface rounded-xl border border-white/[0.07] p-5">
      <p className="text-xs text-secondary uppercase tracking-wider">{label}</p>
      <p className="text-3xl font-bold text-primary mt-2">{value}</p>
      {sub && <p className="text-xs text-muted mt-1">{sub}</p>}
    </div>
  )
}
