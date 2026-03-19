export type ContentStatus = 'draft' | 'queued' | 'publishing' | 'success' | 'partial_success' | 'failed';
export type Platform = 'fb' | 'ig' | 'x' | 'line';

export interface Content {
  id: string;
  title: string;
  master_caption: string;
  image_url: string | null;
  platforms: Platform[];
  publish_at: string | null;
  status: ContentStatus;
  fb_caption: string | null;
  ig_caption: string | null;
  x_caption: string | null;
  line_message: string | null;
  retry_count: number;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublishLog {
  log_id: string;
  content_id: string;
  platform: Platform;
  status: 'success' | 'failed';
  external_post_id: string | null;
  response_summary: string | null;
  created_at: string;
}

export interface MonitorData {
  id: string;
  content_id: string;
  platform: Platform;
  external_post_id: string;
  likes: number;
  comments: number;
  shares: number;
  recent_replies: Reply[];
  fetched_at: string;
}

export interface Reply {
  author: string;
  text: string;
  created_at: string;
  platform: Platform;
}

export const STATUS_LABELS: Record<ContentStatus, string> = {
  draft: '草稿',
  queued: '排程中',
  publishing: '發佈中',
  success: '已發佈',
  partial_success: '部分成功',
  failed: '失敗',
};

export const PLATFORM_LABELS: Record<Platform, string> = {
  fb: 'Facebook',
  ig: 'Instagram',
  x: 'X',
  line: 'LINE',
};

export const PLATFORM_COLORS: Record<Platform, string> = {
  fb: 'bg-info',
  ig: 'bg-primary',
  x: 'bg-foreground',
  line: 'bg-success',
};
