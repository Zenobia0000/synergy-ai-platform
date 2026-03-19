import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Platform, PLATFORM_LABELS } from '@/types/content';
import { useContent, useCreateContent, useUpdateContent, usePublishContent, useScheduleContent } from '@/hooks/use-contents';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { ArrowLeft, Calendar, Image, Send, Save, Loader2 } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';

const platformOptions: { value: Platform; label: string; maxLen?: number }[] = [
  { value: 'fb', label: 'Facebook' },
  { value: 'ig', label: 'Instagram' },
  { value: 'x', label: 'X (Twitter)', maxLen: 280 },
  { value: 'line', label: 'LINE' },
];

export default function CreateContent() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('id');

  const { data: existingContent } = useContent(editId ?? undefined);
  const createContent = useCreateContent();
  const updateContent = useUpdateContent();
  const publishContent = usePublishContent();
  const scheduleContent = useScheduleContent();

  const [title, setTitle] = useState('');
  const [masterCaption, setMasterCaption] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([]);
  const [publishAt, setPublishAt] = useState('');
  const [platformCaptions, setPlatformCaptions] = useState<Partial<Record<Platform, string>>>({});
  const [activeTab, setActiveTab] = useState('content');
  const [initialized, setInitialized] = useState(false);

  // Load existing content for edit mode
  useEffect(() => {
    if (existingContent && !initialized) {
      setTitle(existingContent.title);
      setMasterCaption(existingContent.master_caption);
      setImageUrl(existingContent.image_url ?? '');
      setSelectedPlatforms(existingContent.platforms);
      setPublishAt(existingContent.publish_at ? existingContent.publish_at.slice(0, 16) : '');
      setPlatformCaptions({
        fb: existingContent.fb_caption ?? '',
        ig: existingContent.ig_caption ?? '',
        x: existingContent.x_caption ?? '',
        line: existingContent.line_message ?? '',
      });
      setInitialized(true);
    }
  }, [existingContent, initialized]);

  const isEditing = !!editId;
  const isSaving = createContent.isPending || updateContent.isPending;

  const togglePlatform = (p: Platform) => {
    setSelectedPlatforms(prev =>
      prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
    );
  };

  const validate = (): boolean => {
    if (!title.trim()) {
      toast.error('請輸入標題');
      return false;
    }
    if (!masterCaption.trim()) {
      toast.error('請輸入母文案');
      return false;
    }
    if (selectedPlatforms.length === 0) {
      toast.error('請至少選擇一個平台');
      return false;
    }
    const xCaption = platformCaptions.x;
    if (xCaption && xCaption.length > 280) {
      toast.error('X 文案不可超過 280 字元');
      return false;
    }
    return true;
  };

  const buildPayload = () => ({
    title,
    master_caption: masterCaption,
    image_url: imageUrl || null,
    platforms: selectedPlatforms,
    fb_caption: platformCaptions.fb || null,
    ig_caption: platformCaptions.ig || null,
    x_caption: platformCaptions.x || null,
    line_message: platformCaptions.line || null,
  });

  const handleSave = async () => {
    if (!validate()) return;

    try {
      if (isEditing) {
        await updateContent.mutateAsync({ id: editId!, data: buildPayload() });
        toast.success('貼文已更新');
      } else {
        await createContent.mutateAsync(buildPayload());
        toast.success('貼文已儲存為草稿');
      }
      navigate('/');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '儲存失敗';
      toast.error(message);
    }
  };

  const handlePublish = async () => {
    if (!validate()) return;

    try {
      let contentId = editId;

      if (isEditing) {
        await updateContent.mutateAsync({ id: editId!, data: buildPayload() });
      } else {
        const created = await createContent.mutateAsync(buildPayload());
        contentId = created.id;
      }

      if (publishAt) {
        // Schedule
        const isoDate = new Date(publishAt).toISOString();
        await scheduleContent.mutateAsync({ id: contentId!, publish_at: isoDate });
        toast.success('貼文已排程');
      } else {
        // Publish now
        await publishContent.mutateAsync(contentId!);
        toast.success('發佈已觸發');
      }
      navigate('/');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '發佈失敗';
      toast.error(message);
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')} className="shrink-0">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-display font-semibold text-foreground">
              {isEditing ? '編輯貼文' : '建立貼文'}
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">撰寫內容並設定跨平台發佈</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleSave} disabled={isSaving} className="gap-2">
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isEditing ? '更新' : '儲存草稿'}
          </Button>
          <Button onClick={handlePublish} disabled={isSaving} className="gap-2">
            <Send className="w-4 h-4" />
            {publishAt ? '排程發佈' : '立即發佈'}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-muted">
          <TabsTrigger value="content">內容編輯</TabsTrigger>
          <TabsTrigger value="platform">平台文案</TabsTrigger>
          <TabsTrigger value="preview">預覽</TabsTrigger>
        </TabsList>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main content area */}
            <div className="lg:col-span-2 space-y-5">
              <div className="bg-card rounded-xl border border-border/40 p-5 space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="title">標題 <span className="text-destructive">*</span></Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="輸入貼文標題..."
                    className="bg-background"
                    maxLength={200}
                  />
                  <p className="text-xs text-muted-foreground text-right">{title.length}/200</p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="caption">母文案 <span className="text-destructive">*</span></Label>
                  <Textarea
                    id="caption"
                    value={masterCaption}
                    onChange={e => setMasterCaption(e.target.value)}
                    placeholder="輸入主要文案內容，各平台將以此為基礎..."
                    className="bg-background min-h-[200px] resize-y"
                    maxLength={10000}
                  />
                  <p className="text-xs text-muted-foreground text-right">{masterCaption.length}/10,000</p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="image">圖片網址</Label>
                  <div className="flex gap-2">
                    <Input
                      id="image"
                      value={imageUrl}
                      onChange={e => setImageUrl(e.target.value)}
                      placeholder="https://..."
                      className="bg-background flex-1"
                    />
                    <Button variant="outline" size="icon" className="shrink-0">
                      <Image className="w-4 h-4" />
                    </Button>
                  </div>
                  {imageUrl && (
                    <div className="mt-3 rounded-lg overflow-hidden border border-border/40 aspect-video">
                      <img src={imageUrl} alt="預覽" className="w-full h-full object-cover" onError={e => (e.currentTarget.style.display = 'none')} />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Sidebar settings */}
            <div className="space-y-5">
              {/* Platforms */}
              <div className="bg-card rounded-xl border border-border/40 p-5 space-y-3">
                <Label>目標平台 <span className="text-destructive">*</span></Label>
                <div className="space-y-2.5">
                  {platformOptions.map(p => (
                    <label key={p.value} className="flex items-center gap-2.5 cursor-pointer group">
                      <Checkbox
                        checked={selectedPlatforms.includes(p.value)}
                        onCheckedChange={() => togglePlatform(p.value)}
                      />
                      <span className="text-sm text-foreground group-hover:text-primary transition-colors">
                        {p.label}
                      </span>
                      {p.maxLen && (
                        <span className="text-xs text-muted-foreground ml-auto">{p.maxLen} 字</span>
                      )}
                    </label>
                  ))}
                </div>
              </div>

              {/* Schedule */}
              <div className="bg-card rounded-xl border border-border/40 p-5 space-y-3">
                <Label htmlFor="schedule">排程時間</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                  <Input
                    id="schedule"
                    type="datetime-local"
                    value={publishAt}
                    onChange={e => setPublishAt(e.target.value)}
                    className="bg-background pl-9"
                  />
                </div>
                <p className="text-xs text-muted-foreground">留空則儲存為草稿，填寫後可排程發佈</p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Platform Captions Tab */}
        <TabsContent value="platform" className="space-y-5 mt-6">
          {selectedPlatforms.length === 0 ? (
            <div className="bg-card rounded-xl border border-border/40 p-10 text-center">
              <p className="text-muted-foreground">請先在「內容編輯」分頁選擇目標平台</p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                為各平台設定專屬文案。留空則使用母文案。
              </p>
              {selectedPlatforms.map(p => {
                const opt = platformOptions.find(o => o.value === p)!;
                const caption = platformCaptions[p] || '';
                return (
                  <div key={p} className="bg-card rounded-xl border border-border/40 p-5 space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>{opt.label} 專屬文案</Label>
                      {opt.maxLen && (
                        <span className={`text-xs ${caption.length > opt.maxLen ? 'text-destructive font-medium' : 'text-muted-foreground'}`}>
                          {caption.length}/{opt.maxLen}
                        </span>
                      )}
                    </div>
                    <Textarea
                      value={caption}
                      onChange={e => setPlatformCaptions(prev => ({ ...prev, [p]: e.target.value }))}
                      placeholder={`輸入 ${opt.label} 專屬文案（選填）...`}
                      className="bg-background min-h-[120px] resize-y"
                      maxLength={opt.maxLen}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {selectedPlatforms.length === 0 ? (
              <div className="col-span-full bg-card rounded-xl border border-border/40 p-10 text-center">
                <p className="text-muted-foreground">請先選擇目標平台以預覽</p>
              </div>
            ) : (
              selectedPlatforms.map(p => {
                const opt = platformOptions.find(o => o.value === p)!;
                const caption = platformCaptions[p] || masterCaption;
                return (
                  <div key={p} className="bg-card rounded-xl border border-border/40 overflow-hidden">
                    <div className="px-4 py-3 border-b border-border/30 bg-muted/30">
                      <span className="text-sm font-medium">{opt.label}</span>
                    </div>
                    {imageUrl && (
                      <div className="aspect-video">
                        <img src={imageUrl} alt="" className="w-full h-full object-cover" />
                      </div>
                    )}
                    <div className="p-4 space-y-2">
                      <p className="text-sm font-semibold font-display">{title || '（未填寫標題）'}</p>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                        {caption || '（未填寫文案）'}
                      </p>
                      {p === 'x' && caption.length > 280 && (
                        <p className="text-xs text-destructive">超過 280 字元限制</p>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
