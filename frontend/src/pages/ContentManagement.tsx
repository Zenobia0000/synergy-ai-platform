import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ContentCard } from '@/components/ContentCard';
import { StatusBadge } from '@/components/StatusBadge';
import { PlatformTag } from '@/components/PlatformTag';
import { ContentPreviewDialog } from '@/components/ContentPreviewDialog';
import { useContents, useDeleteContent, usePublishContent } from '@/hooks/use-contents';
import { Content, Platform } from '@/types/content';
import { Plus, Search, Filter, Loader2, LayoutGrid, List as ListIcon, MoreHorizontal, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';

type PlatformFilter = Platform | 'all';
type ViewMode = 'grid' | 'list';

const platformFilters: { label: string; value: PlatformFilter }[] = [
  { label: '全部', value: 'all' },
  { label: 'Facebook', value: 'fb' },
  { label: 'Instagram', value: 'ig' },
  { label: 'X (Twitter)', value: 'x' },
  { label: 'LINE', value: 'line' },
];

const VIEW_MODE_KEY = 'content-view-mode';

export default function ContentManagement() {
  const navigate = useNavigate();
  const [activePlatform, setActivePlatform] = useState<PlatformFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem(VIEW_MODE_KEY) : null;
    return saved === 'list' ? 'list' : 'grid';
  });
  const [previewContent, setPreviewContent] = useState<Content | null>(null);

  const { data, isLoading, isError } = useContents({
    sort_by: '-created_at',
  });

  const deleteContent = useDeleteContent();
  const publishContent = usePublishContent();

  const contents = data?.items ?? [];

  const filteredContents = contents.filter(c => {
    if (activePlatform !== 'all' && !c.platforms.includes(activePlatform)) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return c.title.toLowerCase().includes(q) || c.master_caption.toLowerCase().includes(q);
  });

  const handleDelete = (id: string) => {
    deleteContent.mutate(id, {
      onSuccess: () => toast.success('貼文已刪除'),
      onError: (err) => toast.error(err.message),
    });
  };

  const handlePublish = (id: string) => {
    publishContent.mutate(id, {
      onSuccess: () => toast.success('發佈已觸發'),
      onError: (err) => toast.error(err.message),
    });
  };

  const switchView = (mode: ViewMode) => {
    setViewMode(mode);
    try {
      localStorage.setItem(VIEW_MODE_KEY, mode);
    } catch {
      /* ignore */
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-foreground">貼文管理</h1>
          <p className="text-sm text-muted-foreground mt-1">
            管理你的跨平台內容
            {data && <span className="ml-2">({filteredContents.length} / {data.total} 筆)</span>}
          </p>
        </div>
        <Button className="gap-2 rounded-lg shadow-sm" onClick={() => navigate('/create')}>
          <Plus className="w-4 h-4" />
          建立貼文
        </Button>
      </div>

      {/* Search & Filter & View Toggle */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜尋貼文..."
            className="pl-9 bg-card border-border/40"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 flex-1">
          {platformFilters.map(f => (
            <button
              key={f.value}
              onClick={() => setActivePlatform(f.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                activePlatform === f.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-accent'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="inline-flex rounded-lg border border-border/40 bg-card p-0.5 shrink-0">
          <button
            onClick={() => switchView('grid')}
            title="卡片檢視"
            className={`p-1.5 rounded-md transition-colors ${
              viewMode === 'grid'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => switchView('list')}
            title="條列檢視"
            className={`p-1.5 rounded-md transition-colors ${
              viewMode === 'list'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            <ListIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-destructive">無法載入貼文，請確認後端服務是否運行中</p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && filteredContents.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Filter className="w-10 h-10 text-muted-foreground/40 mb-3" />
          <p className="text-muted-foreground">沒有符合條件的貼文</p>
        </div>
      )}

      {/* Grid View */}
      {!isLoading && !isError && filteredContents.length > 0 && viewMode === 'grid' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredContents.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onPreview={() => setPreviewContent(content)}
              onEdit={() => navigate(`/create?id=${content.id}`)}
              onDelete={() => handleDelete(content.id)}
              onPublish={() => handlePublish(content.id)}
            />
          ))}
        </div>
      )}

      {/* List View */}
      {!isLoading && !isError && filteredContents.length > 0 && viewMode === 'list' && (
        <div className="bg-card rounded-xl border border-border/40 overflow-hidden divide-y divide-border/40">
          {filteredContents.map((content) => (
            <div
              key={content.id}
              onClick={() => setPreviewContent(content)}
              className="flex items-center gap-4 p-3 hover:bg-muted/30 transition-colors group cursor-pointer"
            >
              {/* Thumbnail */}
              <div className="w-16 h-16 shrink-0 rounded-md overflow-hidden bg-muted/30 flex items-center justify-center">
                {content.image_url ? (
                  <img
                    src={content.image_url}
                    alt={content.title}
                    className="w-full h-full object-cover"
                    onError={e => (e.currentTarget.style.display = 'none')}
                  />
                ) : (
                  <span className="text-[10px] text-muted-foreground">無圖</span>
                )}
              </div>

              {/* Title + Caption */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <StatusBadge status={content.status} />
                  <h3 className="font-display font-semibold text-sm text-card-foreground truncate">
                    {content.title}
                  </h3>
                </div>
                <p className="text-xs text-muted-foreground truncate">
                  {content.master_caption}
                </p>
              </div>

              {/* Platforms */}
              <div className="hidden md:flex flex-wrap gap-1 max-w-[180px] justify-end">
                {content.platforms.map(p => (
                  <PlatformTag key={p} platform={p} />
                ))}
              </div>

              {/* Date */}
              {content.publish_at && (
                <div className="hidden lg:flex items-center gap-1.5 text-xs text-muted-foreground shrink-0 w-32">
                  <Calendar className="w-3.5 h-3.5" strokeWidth={1.5} />
                  <span>{formatDate(content.publish_at)}</span>
                </div>
              )}

              {/* Actions */}
              <div onClick={(e) => e.stopPropagation()}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => navigate(`/create?id=${content.id}`)}>
                    編輯
                  </DropdownMenuItem>
                  {content.status === 'draft' && (
                    <>
                      <DropdownMenuItem onClick={() => handlePublish(content.id)}>
                        立即發佈
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => handleDelete(content.id)}
                      >
                        刪除
                      </DropdownMenuItem>
                    </>
                  )}
                  {(content.status === 'failed' || content.status === 'partial_success') && (
                    <DropdownMenuItem onClick={() => handlePublish(content.id)}>
                      重新發佈
                    </DropdownMenuItem>
                  )}
                  {content.status === 'failed' && (
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() => handleDelete(content.id)}
                    >
                      刪除
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Dialog */}
      <ContentPreviewDialog
        content={previewContent}
        open={!!previewContent}
        onOpenChange={(open) => !open && setPreviewContent(null)}
      />
    </div>
  );
}
