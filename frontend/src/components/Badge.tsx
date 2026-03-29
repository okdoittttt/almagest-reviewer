interface BadgeProps {
  label: string
  variant?: 'green' | 'yellow' | 'red' | 'blue' | 'gray' | 'purple'
}

const variantClasses: Record<string, string> = {
  green:  'bg-green-950/60 text-success ring-1 ring-green-900/80',
  yellow: 'bg-yellow-950/60 text-warning ring-1 ring-yellow-900/80',
  red:    'bg-red-950/60 text-danger ring-1 ring-red-900/80',
  blue:   'bg-blue-950/60 text-accent ring-1 ring-blue-900/80',
  gray:   'bg-surface2 text-secondary',
  purple: 'bg-purple-950/60 text-purple-400 ring-1 ring-purple-900/80',
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

const triggerSourceLabels: Record<string, string> = {
  push: '커밋',
  ready_for_review: 'Ready for Review',
  re_review_command: '/re-review',
  label_removed: '라벨 제거',
}

export function TriggerSourceBadge({ source }: { source: string }) {
  const label = triggerSourceLabels[source] ?? source
  return <Badge label={label} variant="purple" />
}
