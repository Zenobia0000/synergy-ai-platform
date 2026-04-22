import type { ApiResponse } from "./api-client";
import { ApiError } from "./api-client";

const BASE_URL = "/api/v1";

export interface UploadImageResult {
  key: string;
  url: string;
  size: number;
  content_type: string;
}

/**
 * Upload an image file to the backend (which stores it in MinIO and
 * returns a public URL via the configured PUBLIC_BASE_URL tunnel).
 *
 * Uses raw fetch with multipart/form-data — the shared `api` client
 * sets Content-Type: application/json which doesn't fit here.
 */
export async function uploadImage(file: File): Promise<UploadImageResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/uploads/image`, {
    method: "POST",
    body: formData,
  });

  let json: ApiResponse<UploadImageResult> | null = null;
  try {
    json = (await response.json()) as ApiResponse<UploadImageResult>;
  } catch {
    throw new ApiError(
      "伺服器發生未預期的錯誤，請稍後再試",
      "server_error",
      response.status
    );
  }

  if (!response.ok || !json.success || !json.data) {
    throw new ApiError(
      json.error?.message ?? "上傳失敗",
      json.error?.code ?? "upload_failed",
      response.status
    );
  }

  return json.data;
}
