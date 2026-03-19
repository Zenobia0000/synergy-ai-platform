import type { Content, Platform } from "@/types/content";
import { api } from "./api-client";

// Backend uses comma-separated string, frontend uses array
interface ContentApiPayload {
  title: string;
  master_caption: string;
  image_url?: string | null;
  platforms: string; // "fb,x,line"
  publish_at?: string | null;
  fb_caption?: string | null;
  ig_caption?: string | null;
  x_caption?: string | null;
  line_message?: string | null;
}

interface ContentApiResponse {
  id: string;
  title: string;
  master_caption: string;
  image_url: string | null;
  platforms: string; // "fb,x,line"
  publish_at: string | null;
  status: string;
  fb_caption: string | null;
  ig_caption: string | null;
  x_caption: string | null;
  line_message: string | null;
  retry_count: number;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

function toContent(raw: ContentApiResponse): Content {
  return {
    ...raw,
    platforms: raw.platforms.split(",") as Platform[],
    status: raw.status as Content["status"],
  };
}

export interface ListContentsParams {
  page?: number;
  limit?: number;
  status?: string;
  sort_by?: string;
}

export interface ListContentsResult {
  items: Content[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export const contentApi = {
  async list(params: ListContentsParams = {}): Promise<ListContentsResult> {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.limit) query.set("limit", String(params.limit));
    if (params.status) query.set("status", params.status);
    if (params.sort_by) query.set("sort_by", params.sort_by);

    const qs = query.toString();
    const path = `/contents${qs ? `?${qs}` : ""}`;
    const res = await api.get<ContentApiResponse[]>(path);

    return {
      items: (res.data ?? []).map(toContent),
      total: res.meta?.pagination?.total ?? 0,
      page: res.meta?.pagination?.page ?? 1,
      limit: res.meta?.pagination?.limit ?? 20,
      has_more: res.meta?.pagination?.has_more ?? false,
    };
  },

  async get(id: string): Promise<Content> {
    const res = await api.get<ContentApiResponse>(`/contents/${id}`);
    return toContent(res.data!);
  },

  async create(data: {
    title: string;
    master_caption: string;
    image_url?: string | null;
    platforms: Platform[];
    publish_at?: string | null;
    fb_caption?: string | null;
    ig_caption?: string | null;
    x_caption?: string | null;
    line_message?: string | null;
  }): Promise<Content> {
    const payload: ContentApiPayload = {
      ...data,
      platforms: data.platforms.join(","),
    };
    const res = await api.post<ContentApiResponse>("/contents", payload);
    return toContent(res.data!);
  },

  async update(
    id: string,
    data: Partial<{
      title: string;
      master_caption: string;
      image_url: string | null;
      platforms: Platform[];
      publish_at: string | null;
      status: string;
      fb_caption: string | null;
      ig_caption: string | null;
      x_caption: string | null;
      line_message: string | null;
    }>
  ): Promise<Content> {
    const payload: Record<string, unknown> = { ...data };
    if (data.platforms) {
      payload.platforms = data.platforms.join(",");
    }
    const res = await api.put<ContentApiResponse>(`/contents/${id}`, payload);
    return toContent(res.data!);
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/contents/${id}`);
  },

  async schedule(id: string, publish_at: string): Promise<Content> {
    const res = await api.post<ContentApiResponse>(`/contents/${id}/schedule`, {
      publish_at,
    });
    return toContent(res.data!);
  },

  async cancelSchedule(id: string): Promise<Content> {
    const res = await api.delete<ContentApiResponse>(
      `/contents/${id}/schedule`
    );
    return toContent(res.data!);
  },

  async publish(id: string): Promise<Content> {
    const res = await api.post<ContentApiResponse>(
      `/contents/${id}/publish`
    );
    return toContent(res.data!);
  },
};
