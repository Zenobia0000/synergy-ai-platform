import { Content, Platform, PLATFORM_LABELS } from '@/types/content';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlatformPreview } from './PlatformPreview';
import { StatusBadge } from './StatusBadge';
import { useState, useEffect } from 'react';

interface ContentPreviewDialogProps {
  content: Content | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ContentPreviewDialog({ content, open, onOpenChange }: ContentPreviewDialogProps) {
  const platforms: Platform[] = content?.platforms ?? [];
  const [activePlatform, setActivePlatform] = useState<Platform | undefined>(platforms[0]);

  // Reset active tab whenever the content (and thus its platforms) changes
  useEffect(() => {
    if (platforms.length > 0) {
      setActivePlatform(platforms[0]);
    }
  }, [content?.id]);

  if (!content) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3 flex-wrap">
            <DialogTitle className="text-left">{content.title}</DialogTitle>
            <StatusBadge status={content.status} />
          </div>
          <p className="text-xs text-muted-foreground text-left">
            預覽僅為示意，實際呈現以各平台為準
          </p>
        </DialogHeader>

        {platforms.length === 0 ? (
          <div className="py-10 text-center text-muted-foreground">未選擇任何平台</div>
        ) : (
          <Tabs
            value={activePlatform}
            onValueChange={(v) => setActivePlatform(v as Platform)}
            className="flex flex-col items-center gap-4"
          >
            <TabsList className="bg-muted">
              {platforms.map((p) => (
                <TabsTrigger key={p} value={p}>
                  {PLATFORM_LABELS[p]}
                </TabsTrigger>
              ))}
            </TabsList>
            {platforms.map((p) => (
              <TabsContent key={p} value={p} className="w-full mt-0 pb-2 flex justify-center">
                <PlatformPreview content={content} platform={p} />
              </TabsContent>
            ))}
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
