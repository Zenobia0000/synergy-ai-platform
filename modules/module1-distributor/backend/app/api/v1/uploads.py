"""Image upload + proxy endpoints.

Flow:
  Frontend  -- POST /uploads/image (multipart)        --> Backend
  Backend   -- put_object()                            --> MinIO
  Backend   -- {url: PUBLIC_BASE_URL/uploads/{key}}    --> Frontend

  Instagram -- GET PUBLIC_BASE_URL/uploads/{key}       --> ngrok tunnel
  ngrok     -- forward                                 --> Backend
  Backend   -- get_object_stream() + StreamingResponse --> Instagram
"""

from __future__ import annotations

import logging
import uuid
from pathlib import PurePosixPath

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from minio.error import S3Error

from app.schemas.response import error_response, success_response
from app.services import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB — Instagram's hard limit
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Accept a multipart image upload, persist to MinIO, return public URL."""
    # Validate filename / extension
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error",
                "filename_missing",
                "缺少檔案名稱",
                param="file",
            ),
        )

    ext = PurePosixPath(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error",
                "unsupported_image_format",
                f"不支援的圖片格式 .{ext}，僅接受 jpg/jpeg/png",
                param="file",
            ),
        )

    # Validate content-type if browser sent one
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error",
                "unsupported_content_type",
                f"不支援的 content type {file.content_type}",
                param="file",
            ),
        )

    # Read body, enforce size limit
    body = await file.read()
    if len(body) > MAX_IMAGE_BYTES:
        return JSONResponse(
            status_code=413,
            content=error_response(
                "invalid_request_error",
                "image_too_large",
                f"圖片大小超過 8 MB 上限（{len(body) / 1024 / 1024:.1f} MB）",
                param="file",
            ),
        )

    if len(body) == 0:
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error",
                "empty_file",
                "檔案為空",
                param="file",
            ),
        )

    # Use deterministic content type for IG compat
    normalized_content_type = "image/jpeg" if ext in {"jpg", "jpeg"} else "image/png"

    # Generate stable key — uuid keeps URLs unguessable + collision-free
    key = f"{uuid.uuid4().hex}.{'jpg' if ext in {'jpg', 'jpeg'} else 'png'}"

    try:
        await storage_service.put_object(key, body, normalized_content_type)
    except S3Error as e:
        logger.exception("MinIO upload failed for key %s", key)
        return JSONResponse(
            status_code=503,
            content=error_response(
                "storage_error",
                "minio_upload_failed",
                f"物件儲存上傳失敗：{e.code}",
            ),
        )

    relative_url = storage_service.build_relative_url(key)
    return success_response(
        {
            "key": key,
            # Frontend stores this in DB; backend rewrites to absolute
            # via PUBLIC_BASE_URL when triggering n8n / Instagram.
            "url": relative_url,
            "size": len(body),
            "content_type": normalized_content_type,
        }
    )


@router.get("/{key}")
async def get_image(key: str):
    """Stream an uploaded image from MinIO.

    This endpoint is the public-facing proxy that Instagram fetches via
    the ngrok / cloudflared tunnel. Keeps MinIO fully private; only the
    backend touches it.
    """
    # Defensive: don't allow path traversal
    if "/" in key or ".." in key:
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error",
                "invalid_key",
                "非法的物件鍵",
            ),
        )

    try:
        size, content_type = await storage_service.stat_object(key)
    except S3Error as e:
        if e.code in ("NoSuchKey", "NoSuchObject"):
            return JSONResponse(
                status_code=404,
                content=error_response("not_found", "image_not_found", "圖片不存在"),
            )
        logger.exception("MinIO stat failed for key %s", key)
        return JSONResponse(
            status_code=503,
            content=error_response(
                "storage_error",
                "minio_stat_failed",
                f"物件儲存查詢失敗：{e.code}",
            ),
        )

    def _iter_bytes():
        response = storage_service.get_object_stream(key)
        try:
            for chunk in response.stream(amt=64 * 1024):
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return StreamingResponse(
        _iter_bytes(),
        media_type=content_type,
        headers={
            "Content-Length": str(size),
            # Allow Meta crawlers + reasonable caching
            "Cache-Control": "public, max-age=3600",
        },
    )
