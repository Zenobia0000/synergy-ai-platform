import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ContentCard } from '@/components/ContentCard';
import { useContents, useDeleteContent, usePublishContent } from '@/hooks/use-contents';
import { ContentStatus } from '@/types/content';
import { Plus, Search, Filter, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';

const statusFilters: { label: string; value: ContentStatus | 'all' }[] = [
  { label: '全部', value: 'all' },
  { label: '草稿', value: 'draft' },
  { label: '排程中', value: 'queued' },
  { label: '已發佈', value: 'success' },
  { label: '部分成功', value: 'partial_success' },
  { label: '失敗', value: 'failed' },
];

export default function ContentManagement() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState<ContentStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, isError } = useContents({
    status: activeFilter === 'all' ? undefined : activeFilter,
    sort_by: '-created_at',
  });

  const deleteContent = useDeleteContent();
  const publishContent = usePublishContent();

  const contents = data?.items ?? [];

  const filteredContents = contents.filter(c => {
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

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-foreground">貼文管理</h1>
          <p className="text-sm text-muted-foreground mt-1">
            管理你的跨平台內容
            {data && <span className="ml-2">({data.total} 筆)</span>}
          </p>
        </div>
        <Button className="gap-2 rounded-lg shadow-sm" onClick={() => navigate('/create')}>
          <Plus className="w-4 h-4" />
          建立貼文
        </Button>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜尋貼文..."
            className="pl-9 bg-card border-border/40"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {statusFilters.map(f => (
            <button
              key={f.value}
              onClick={() => setActiveFilter(f.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                activeFilter === f.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-accent'
              }`}
            >
              {f.label}
            </button>
          ))}
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

      {/* Gallery Grid */}
      {!isLoading && !isError && filteredContents.length > 0 && (
        <div className="columns-1 sm:columns-2 lg:columns-3 gap-4 space-y-4">
          {filteredContents.map((content, i) => (
            <div key={content.id} className="break-inside-avoid" style={{ animationDelay: `${i * 80}ms` }}>
              <ContentCard
                content={content}
                onEdit={() => navigate(`/create?id=${content.id}`)}
                onDelete={() => handleDelete(content.id)}
                onPublish={() => handlePublish(content.id)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
