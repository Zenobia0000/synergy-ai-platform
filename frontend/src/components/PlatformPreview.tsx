import { Content, Platform } from '@/types/content';
import {
  Heart,
  MessageCircle,
  Send,
  Bookmark,
  ThumbsUp,
  Share2,
  Repeat2,
  BarChart2,
  MoreHorizontal,
} from 'lucide-react';

interface PlatformPreviewProps {
  content: Pick<
    Content,
    'title' | 'master_caption' | 'image_url' | 'fb_caption' | 'ig_caption' | 'x_caption' | 'line_message'
  >;
  platform: Platform;
  /** 顯示的虛擬帳號名稱（之後可從 settings 帶入） */
  accountName?: string;
  accountHandle?: string;
}

const captionFor = (content: PlatformPreviewProps['content'], platform: Platform): string => {
  switch (platform) {
    case 'fb':
      return content.fb_caption || content.master_caption;
    case 'ig':
      return content.ig_caption || content.master_caption;
    case 'x':
      return content.x_caption || content.master_caption;
    case 'line':
      return content.line_message || content.master_caption;
  }
};

/* ---------------- Facebook ---------------- */
function FacebookPreview({ content, accountName = 'Your Page' }: { content: PlatformPreviewProps['content']; accountName?: string }) {
  const caption = captionFor(content, 'fb');
  return (
    <div className="bg-white text-[#050505] rounded-lg border border-[#dddfe2] overflow-hidden w-full max-w-[420px] mx-auto shadow-sm">
      {/* Header */}
      <div className="p-3 flex items-center gap-2">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-semibold">
          {accountName.charAt(0)}
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold leading-tight">{accountName}</p>
          <p className="text-xs text-[#65676b]">剛剛 · 公開</p>
        </div>
        <MoreHorizontal className="w-5 h-5 text-[#65676b]" />
      </div>

      {/* Title + Caption */}
      <div className="px-3 pb-3">
        {content.title && <p className="text-[15px] font-semibold mb-1">{content.title}</p>}
        <p className="text-[15px] whitespace-pre-wrap leading-relaxed">{caption || '（未填寫文案）'}</p>
      </div>

      {/* Image */}
      {content.image_url && (
        <div className="bg-black flex items-center justify-center">
          <img src={content.image_url} alt="" className="max-w-full max-h-[360px] object-contain" />
        </div>
      )}

      {/* Reactions row */}
      <div className="px-3 py-2 flex items-center justify-between text-xs text-[#65676b] border-b border-[#ced0d4]">
        <div className="flex items-center gap-1">
          <span className="w-4 h-4 rounded-full bg-blue-500 inline-flex items-center justify-center">
            <ThumbsUp className="w-2.5 h-2.5 text-white fill-white" />
          </span>
          <span>0</span>
        </div>
        <span>0 則留言 · 0 次分享</span>
      </div>
      <div className="grid grid-cols-3 px-3 py-1 text-[#65676b] text-sm">
        <button className="flex items-center justify-center gap-2 py-2 hover:bg-[#f2f2f2] rounded-md">
          <ThumbsUp className="w-5 h-5" /> 讚
        </button>
        <button className="flex items-center justify-center gap-2 py-2 hover:bg-[#f2f2f2] rounded-md">
          <MessageCircle className="w-5 h-5" /> 留言
        </button>
        <button className="flex items-center justify-center gap-2 py-2 hover:bg-[#f2f2f2] rounded-md">
          <Share2 className="w-5 h-5" /> 分享
        </button>
      </div>
    </div>
  );
}

/* ---------------- Instagram ---------------- */
function InstagramPreview({ content, accountName = 'your_account' }: { content: PlatformPreviewProps['content']; accountName?: string }) {
  const caption = captionFor(content, 'ig');
  return (
    <div className="bg-white text-black rounded-lg border border-[#dbdbdb] overflow-hidden w-full max-w-[380px] mx-auto shadow-sm">
      {/* Header */}
      <div className="p-3 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full p-[2px] bg-gradient-to-tr from-yellow-400 via-red-500 to-purple-600">
          <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
            <div className="w-[26px] h-[26px] rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white text-xs font-semibold">
              {accountName.charAt(0).toUpperCase()}
            </div>
          </div>
        </div>
        <p className="text-sm font-semibold flex-1">{accountName}</p>
        <MoreHorizontal className="w-5 h-5" />
      </div>

      {/* Square image */}
      <div className="aspect-square bg-black flex items-center justify-center">
        {content.image_url ? (
          <img src={content.image_url} alt="" className="max-w-full max-h-full object-contain" />
        ) : (
          <span className="text-white/60 text-sm">Instagram 必須有圖片</span>
        )}
      </div>

      {/* Action row */}
      <div className="px-3 pt-3 flex items-center gap-4">
        <Heart className="w-6 h-6" strokeWidth={1.8} />
        <MessageCircle className="w-6 h-6" strokeWidth={1.8} />
        <Send className="w-6 h-6" strokeWidth={1.8} />
        <Bookmark className="w-6 h-6 ml-auto" strokeWidth={1.8} />
      </div>

      {/* Likes + Caption */}
      <div className="px-3 py-2 space-y-1">
        <p className="text-sm font-semibold">0 個讚</p>
        <p className="text-sm whitespace-pre-wrap leading-relaxed">
          <span className="font-semibold mr-1.5">{accountName}</span>
          {caption || '（未填寫文案）'}
        </p>
        <p className="text-xs text-[#8e8e8e] uppercase pt-1">剛剛</p>
      </div>
    </div>
  );
}

/* ---------------- X (Twitter) ---------------- */
function XPreview({ content, accountName = 'Your Name', accountHandle = 'your_handle' }: { content: PlatformPreviewProps['content']; accountName?: string; accountHandle?: string }) {
  const caption = captionFor(content, 'x');
  const overLimit = caption.length > 280;
  return (
    <div className="bg-white text-[#0f1419] rounded-2xl border border-[#eff3f4] overflow-hidden w-full max-w-[460px] mx-auto shadow-sm">
      <div className="p-4 flex gap-3">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-black shrink-0 flex items-center justify-center text-white font-semibold">
          {accountName.charAt(0)}
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-1 text-[15px] leading-tight">
            <span className="font-bold">{accountName}</span>
            <span className="text-[#536471]">@{accountHandle} · 剛剛</span>
            <MoreHorizontal className="w-4 h-4 text-[#536471] ml-auto" />
          </div>

          {/* Text */}
          <p className={`mt-1 text-[15px] whitespace-pre-wrap leading-relaxed ${overLimit ? 'text-destructive' : ''}`}>
            {caption || '（未填寫文案）'}
          </p>
          {overLimit && (
            <p className="text-xs text-destructive mt-1">超過 280 字限制（{caption.length} 字）</p>
          )}

          {/* Image */}
          {content.image_url && (
            <div className="mt-3 rounded-2xl overflow-hidden border border-[#eff3f4] bg-black flex items-center justify-center">
              <img src={content.image_url} alt="" className="max-w-full max-h-[340px] object-contain" />
            </div>
          )}

          {/* Action row */}
          <div className="mt-3 flex items-center justify-between text-[#536471] text-sm max-w-md">
            <button className="flex items-center gap-1.5 hover:text-blue-500">
              <MessageCircle className="w-[18px] h-[18px]" /> 0
            </button>
            <button className="flex items-center gap-1.5 hover:text-green-500">
              <Repeat2 className="w-[18px] h-[18px]" /> 0
            </button>
            <button className="flex items-center gap-1.5 hover:text-pink-500">
              <Heart className="w-[18px] h-[18px]" /> 0
            </button>
            <button className="flex items-center gap-1.5 hover:text-blue-500">
              <BarChart2 className="w-[18px] h-[18px]" /> 0
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------- LINE ---------------- */
function LinePreview({ content, accountName = 'Your OA' }: { content: PlatformPreviewProps['content']; accountName?: string }) {
  const caption = captionFor(content, 'line');
  return (
    <div className="bg-[#7494c0] rounded-lg p-4 w-full max-w-[420px] mx-auto">
      {/* OA header bar */}
      <div className="bg-white/95 rounded-t-lg px-3 py-2 flex items-center gap-2 shadow-sm">
        <div className="w-7 h-7 rounded-full bg-[#06c755] flex items-center justify-center text-white text-xs font-bold">
          {accountName.charAt(0)}
        </div>
        <p className="text-sm font-semibold text-[#111]">{accountName}</p>
      </div>

      {/* Chat area */}
      <div className="bg-[#7494c0] py-4 px-2 space-y-2">
        <div className="flex items-end gap-2">
          {/* Avatar */}
          <div className="w-9 h-9 rounded-full bg-[#06c755] flex items-center justify-center text-white text-sm font-bold shrink-0">
            {accountName.charAt(0)}
          </div>
          <div className="space-y-1 max-w-[75%]">
            <p className="text-[11px] text-white/90 px-1">{accountName}</p>
            {/* Image bubble */}
            {content.image_url && (
              <div className="rounded-2xl overflow-hidden bg-black/20">
                <img src={content.image_url} alt="" className="max-w-full max-h-[260px] object-contain" />
              </div>
            )}
            {/* Text bubble */}
            <div className="bg-white rounded-2xl px-3 py-2 shadow-sm">
              {content.title && <p className="text-sm font-semibold text-[#111] mb-1">{content.title}</p>}
              <p className="text-sm text-[#111] whitespace-pre-wrap leading-relaxed">
                {caption || '（未填寫訊息）'}
              </p>
            </div>
          </div>
          <span className="text-[10px] text-white/80 mb-1">剛剛</span>
        </div>
      </div>
    </div>
  );
}

export function PlatformPreview({ content, platform, accountName, accountHandle }: PlatformPreviewProps) {
  switch (platform) {
    case 'fb':
      return <FacebookPreview content={content} accountName={accountName} />;
    case 'ig':
      return <InstagramPreview content={content} accountName={accountName} />;
    case 'x':
      return <XPreview content={content} accountName={accountName} accountHandle={accountHandle} />;
    case 'line':
      return <LinePreview content={content} accountName={accountName} />;
  }
}
