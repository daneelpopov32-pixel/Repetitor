"""
Image download utility for FIPI tasks.

Downloads images from FIPI URLs, saves locally, and returns local paths.
Handles broken images by marking them in metadata.
"""
import os
import re
import hashlib
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# Base directory for downloaded images
MEDIA_DIR = Path("/app/media/images")

# FIPI project ID for EGE History
FIPI_PROJECT_ID = "068A227D253BA6C04D0C832387FD0D89"

# Pattern to extract GUID from bare filenames like xs3docsrc{GUID}_{n}_{ts}.ext
_BARE_DOC_GUID_RE = re.compile(r'xs3docsrc([A-Fa-f0-9]{32})')
_BARE_QST_GUID_RE = re.compile(r'xs3qstsrc([A-Fa-f0-9]{32})')


def _ensure_media_dir():
    """Create media directory if it doesn't exist."""
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def _url_to_filename(url: str) -> str:
    """Generate a deterministic filename from URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    ext = Path(url).suffix or ".jpg"
    return f"{url_hash}{ext}"


def download_image(url: str, timeout: int = 15) -> str | None:
    """Download a single image from URL, save locally, return local path.

    Returns relative path like "images/abc123.jpg" or None on failure.
    """
    if not url:
        return None

    # Resolve relative URLs
    if url.startswith("/"):
        url = f"https://ege.fipi.ru{url}"
    elif url.startswith("../../"):
        url = f"https://ege.fipi.ru/{url[6:]}"  # Remove ../../ and prepend base
    elif url.startswith("docs/"):
        url = f"https://ege.fipi.ru/{url}"
    elif not url.startswith("http"):
        # Bare filename (e.g. xs3docsrc{GUID}_{n}_{ts}.jpg or xs3qstsrc{GUID}_{n}_{ts}.jpg)
        m = _BARE_DOC_GUID_RE.search(url)
        if m:
            guid = m.group(1)
            url = f"https://ege.fipi.ru/docs/{FIPI_PROJECT_ID}/docs/{guid}/{url}"
        else:
            m = _BARE_QST_GUID_RE.search(url)
            if m:
                guid = m.group(1)
                url = f"https://ege.fipi.ru/docs/{FIPI_PROJECT_ID}/questions/{guid}(copy1)/{url}"
            else:
                url = f"https://ege.fipi.ru/bank/{url}"

    filename = _url_to_filename(url)
    local_path = MEDIA_DIR / filename

    # Skip if already downloaded
    if local_path.exists():
        return f"images/{filename}"

    _ensure_media_dir()

    try:
        with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

            # Validate content type
            content_type = resp.headers.get("content-type", "")
            if "image" not in content_type and len(resp.content) < 100:
                logger.warning("URL %s returned non-image content: %s", url, content_type)
                return None

            local_path.write_bytes(resp.content)
            return f"images/{filename}"

    except httpx.TimeoutException:
        logger.warning("Timeout downloading image: %s", url)
        return None
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP error downloading image %s: %s", url, e.response.status_code)
        return None
    except Exception as e:
        logger.warning("Error downloading image %s: %s", url, e)
        return None


def download_task_images(images: list[str]) -> list[str]:
    """Download all images for a task. Returns list of local paths.

    Broken images are replaced with None in the list.
    """
    if not images:
        return []

    local_paths = []
    for url in images:
        path = download_image(url)
        local_paths.append(path)

    return local_paths


def download_task_images_async(images: list[str]) -> list[str]:
    """Async version: download all images for a task.

    Uses httpx.AsyncClient for concurrent downloads.
    """
    if not images:
        return []

    import asyncio

    async def _download_one(url: str) -> str | None:
        if not url:
            return None
        if url.startswith("/"):
            url = f"https://ege.fipi.ru{url}"
        el        if not url.startswith("http"):
            m = _BARE_DOC_GUID_RE.search(url)
            if m:
                guid = m.group(1)
                url = f"https://ege.fipi.ru/docs/{FIPI_PROJECT_ID}/docs/{guid}/{url}"
            else:
                m = _BARE_QST_GUID_RE.search(url)
                if m:
                    guid = m.group(1)
                    url = f"https://ege.fipi.ru/docs/{FIPI_PROJECT_ID}/questions/{guid}(copy1)/{url}"
                else:
                    url = f"https://ege.fipi.ru/bank/{url}"

        filename = _url_to_filename(url)
        local_path = MEDIA_DIR / filename

        if local_path.exists():
            return f"images/{filename}"

        _ensure_media_dir()

        try:
            async with httpx.AsyncClient(timeout=15, verify=False, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                local_path.write_bytes(resp.content)
                return f"images/{filename}"
        except Exception as e:
            logger.warning("Failed to download %s: %s", url, e)
            return None

    loop = asyncio.new_event_loop()
    try:
        tasks = [_download_one(url) for url in images]
        results = loop.run_until_complete(asyncio.gather(*tasks))
        return list(results)
    finally:
        loop.close()
