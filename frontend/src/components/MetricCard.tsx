import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: { value: number; label: string };
  className?: string;
}

export function MetricCard({ title, value, subtitle, icon: Icon, trend, className }: MetricCardProps) {
  return (
    <div className={cn(
      "bg-card rounded-xl border border-border/40 p-5 space-y-3",
      className
    )}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground font-body">{title}</span>
        {Icon && <Icon className="w-4 h-4 text-muted-foreground/60" strokeWidth={1.5} />}
      </div>
      <div>
        <span className="font-display text-3xl font-semibold text-card-foreground tracking-tight">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </div>
      {trend && (
        <div className="flex items-center gap-1">
          <span className={cn(
            "text-xs font-medium",
            trend.value >= 0 ? "text-success" : "text-destructive"
          )}>
            {trend.value >= 0 ? '+' : ''}{trend.value}%
          </span>
          <span className="text-xs text-muted-foreground">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
