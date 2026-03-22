interface BadgeProps {
  label: string
  variant?: 'green' | 'yellow' | 'red' | 'blue' | 'gray' | 'purple'
}

const variantClasses: Record<string, string> = {
  green: 'bg-green-100 text-green-800',
  yellow: 'bg-yellow-100 text-yellow-800',
  red: 'bg-red-100 text-red-800',
  blue: 'bg-blue-100 text-blue-800',
  gray: 'bg-gray-100 text-gray-700',
  purple: 'bg-purple-100 text-purple-800',
}

export function Badge({ label, variant = 'gray' }: BadgeProps) {
  return (
    <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${variantClasses[variant]}`}>
      {label}
    </span>
  )
}

export function RiskBadge({ level }: { level: string | null }) {
  if (!level) return <Badge label="N/A" variant="gray" />
  const map: Record<string, BadgeProps['variant']> = {
    LOW: 'green',
    MEDIUM: 'yellow',
    HIGH: 'red',
  }
  return <Badge label={level} variant={map[level] ?? 'gray'} />
}

export function DecisionBadge({ decision }: { decision: string | null }) {
  if (!decision) return <Badge label="N/A" variant="gray" />
  const map: Record<string, BadgeProps['variant']> = {
    APPROVE: 'green',
    REQUEST_CHANGES: 'red',
    COMMENT: 'blue',
  }
  return <Badge label={decision} variant={map[decision] ?? 'gray'} />
}
