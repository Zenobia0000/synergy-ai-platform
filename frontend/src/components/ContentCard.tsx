import { Content } from '@/types/content';
import { StatusBadge } from './StatusBadge';
import { PlatformTag } from './PlatformTag';
import { Calendar, MoreHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ContentCardProps {
  content: Content;
  onEdit?: () => void;
  onDelete?: () => void;
  onPublish?: () => void;
}

export function ContentCard({ content, onEdit, onDelete, onPublish }: ContentCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="group bg-card rounded-xl overflow-hidden border border-border/40 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300">
      {content.image_url && (
        <div className="aspect-[4/3] overflow-hidden">
          <img
            src={content.image_url}
            alt={content.title}
            className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-500"
          />
        </div>
      )}
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <StatusBadge status={content.status} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onEdit}>編輯</DropdownMenuItem>
              {content.status === 'draft' && (
                <>
                  <DropdownMenuItem onClick={onPublish}>立即發佈</DropdownMenuItem>
                  <DropdownMenuItem className="text-destructive" onClick={onDelete}>刪除</DropdownMenuItem>
                </>
              )}
              {(content.status === 'failed' || content.status === 'partial_success') && (
                <DropdownMenuItem onClick={onPublish}>重新發佈</DropdownMenuItem>
              )}
              {content.status === 'failed' && (
                <DropdownMenuItem className="text-destructive" onClick={onDelete}>刪除</DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <h3 className="font-display font-semibold text-card-foreground leading-snug">
          {content.title}
        </h3>

        <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
          {content.master_caption}
        </p>

        <div className="flex flex-wrap gap-1.5">
          {content.platforms.map(p => (
            <PlatformTag key={p} platform={p} />
          ))}
        </div>

        {content.publish_at && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground pt-1">
            <Calendar className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>{formatDate(content.publish_at)}</span>
          </div>
        )}

        {content.last_error && (
          <p className="text-xs text-destructive bg-destructive/5 rounded-md px-2 py-1.5 leading-relaxed">
            {content.last_error}
          </p>
        )}
      </div>
    </div>
  );
}
