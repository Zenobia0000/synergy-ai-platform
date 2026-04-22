import { ContentStatus, STATUS_LABELS } from '@/types/content';
import { cn } from '@/lib/utils';

const statusStyles: Record<ContentStatus, string> = {
  draft: 'bg-muted text-muted-foreground',
  queued: 'bg-info/15 text-info',
  publishing: 'bg-warning/15 text-warning',
  success: 'bg-success/15 text-success',
  partial_success: 'bg-warning/15 text-warning',
  failed: 'bg-destructive/15 text-destructive',
};

interface StatusBadgeProps {
  status: ContentStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      statusStyles[status],
      className
    )}>
      {STATUS_LABELS[status]}
    </span>
  );
}
