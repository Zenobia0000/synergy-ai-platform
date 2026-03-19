import { Reply } from '@/types/content';
import { PlatformTag } from './PlatformTag';

interface ReplyItemProps {
  reply: Reply;
}

export function ReplyItem({ reply }: ReplyItemProps) {
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex gap-3 py-3 border-b border-border/30 last:border-0">
      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0 text-xs font-medium text-muted-foreground">
        {reply.author.charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-foreground">{reply.author}</span>
          <PlatformTag platform={reply.platform} />
          <span className="text-xs text-muted-foreground">{formatTime(reply.created_at)}</span>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">{reply.text}</p>
      </div>
    </div>
  );
}
