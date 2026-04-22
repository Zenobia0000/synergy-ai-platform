import React from 'react';
import { Platform, PLATFORM_LABELS } from '@/types/content';
import { cn } from '@/lib/utils';

const platformStyles: Record<Platform, string> = {
  fb: 'bg-[hsl(220,60%,50%)]/10 text-[hsl(220,60%,50%)]',
  ig: 'bg-primary/10 text-primary',
  x: 'bg-foreground/10 text-foreground',
  line: 'bg-success/10 text-success',
};

interface PlatformTagProps {
  platform: Platform;
  className?: string;
}

export const PlatformTag = React.forwardRef<HTMLSpanElement, PlatformTagProps>(
  ({ platform, className }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium',
          platformStyles[platform],
          className
        )}
      >
        {PLATFORM_LABELS[platform]}
      </span>
    );
  }
);
PlatformTag.displayName = 'PlatformTag';
