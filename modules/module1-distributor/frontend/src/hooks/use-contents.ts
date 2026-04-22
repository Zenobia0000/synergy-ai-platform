import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { contentApi, type ListContentsParams } from "@/services/content-api";
import type { Content, Platform } from "@/types/content";

// Query keys
export const contentKeys = {
  all: ["contents"] as const,
  lists: () => [...contentKeys.all, "list"] as const,
  list: (params: ListContentsParams) =>
    [...contentKeys.lists(), params] as const,
  details: () => [...contentKeys.all, "detail"] as const,
  detail: (id: string) => [...contentKeys.details(), id] as const,
};

// List contents with polling
export function useContents(params: ListContentsParams = {}) {
  return useQuery({
    queryKey: contentKeys.list(params),
    queryFn: () => contentApi.list(params),
    refetchInterval: 10_000, // Poll every 10s for status updates
  });
}

// Get single content
export function useContent(id: string | undefined) {
  return useQuery({
    queryKey: contentKeys.detail(id!),
    queryFn: () => contentApi.get(id!),
    enabled: !!id,
  });
}

// Create content
export function useCreateContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      title: string;
      master_caption: string;
      image_url?: string | null;
      platforms: Platform[];
      publish_at?: string | null;
      fb_caption?: string | null;
      ig_caption?: string | null;
      x_caption?: string | null;
      line_message?: string | null;
    }) => contentApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
    },
  });
}

// Update content
export function useUpdateContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Content>;
    }) => contentApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: contentKeys.detail(variables.id),
      });
    },
  });
}

// Delete content
export function useDeleteContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => contentApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
    },
  });
}

// Schedule content
export function useScheduleContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, publish_at }: { id: string; publish_at: string }) =>
      contentApi.schedule(id, publish_at),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: contentKeys.detail(variables.id),
      });
    },
  });
}

// Cancel schedule
export function useCancelSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => contentApi.cancelSchedule(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.detail(id) });
    },
  });
}

// Publish content
export function usePublishContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => contentApi.publish(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.detail(id) });
    },
  });
}
