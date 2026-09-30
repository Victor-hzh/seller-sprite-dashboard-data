#!/usr/bin/env python3
"""Upload a Next.js static export to Alibaba Cloud OSS.

Credentials are read from environment variables and are never written to disk.
Matching objects are overwritten, but remote-only objects are not deleted.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import hmac
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import formatdate
from pathlib import Path


DEFAULT_BUCKET = "seller-sprite-dashboard"
DEFAULT_ENDPOINT = "oss-cn-beijing.aliyuncs.com"
DEFAULT_SITE_URL = "https://sellersprite.uwant.cc/"


def env_value(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def cache_control(key: str) -> str:
    if key == "index.html" or key.endswith("/index.html"):
        return "no-cache, no-store, must-revalidate"
    if key.startswith("_next/static/"):
        return "public, max-age=31536000, immutable"
    return "public, max-age=3600"


def content_type(path: Path) -> str:
    overrides = {
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".woff2": "font/woff2",
    }
    return overrides.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def oss_signature(method: str, mime: str, date: str, resource: str, secret: str) -> str:
    string_to_sign = f"{method}\n\n{mime}\n{date}\n{resource}"
    digest = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("ascii")


def upload_one(
    path: Path,
    root: Path,
    bucket: str,
    endpoint: str,
    access_key_id: str,
    access_key_secret: str,
    dry_run: bool,
) -> tuple[str, int]:
    key = path.relative_to(root).as_posix()
    size = path.stat().st_size
    if dry_run:
        return key, size

    mime = content_type(path)
    date = formatdate(usegmt=True)
    quoted_key = urllib.parse.quote(key, safe="/_.-~")
    url = f"https://{bucket}.{endpoint}/{quoted_key}"
    resource = f"/{bucket}/{key}"
    signature = oss_signature("PUT", mime, date, resource, access_key_secret)
    headers = {
        "Authorization": f"OSS {access_key_id}:{signature}",
        "Cache-Control": cache_control(key),
        "Content-Type": mime,
        "Date": date,
    }

    data = path.read_bytes()
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method="PUT")
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status not in (200, 201):
                    raise RuntimeError(f"HTTP {response.status}")
            return key, size
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 2)
    raise RuntimeError(f"上传失败：{key} ({last_error})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload the static out directory to Alibaba Cloud OSS.")
    parser.add_argument("--directory", default="out", help="Static export directory (default: out)")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true", help="List files without uploading")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir() or not (root / "index.html").is_file():
        print(f"错误：{root} 不是有效的静态网站目录，缺少 index.html。", file=sys.stderr)
        return 2

    access_key_id = env_value("ALIYUN_OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_ID")
    access_key_secret = env_value("ALIYUN_OSS_ACCESS_KEY_SECRET", "OSS_ACCESS_KEY_SECRET")
    if not args.dry_run and (not access_key_id or not access_key_secret):
        print("错误：请先设置 ALIYUN_OSS_ACCESS_KEY_ID 和 ALIYUN_OSS_ACCESS_KEY_SECRET。", file=sys.stderr)
        return 2

    files = sorted(path for path in root.rglob("*") if path.is_file())
    # Upload HTML last so it never references assets that are not uploaded yet.
    html_files = [path for path in files if path.suffix.lower() == ".html"]
    asset_files = [path for path in files if path.suffix.lower() != ".html"]

    total_bytes = sum(path.stat().st_size for path in files)
    mode = "检查" if args.dry_run else "上传"
    print(f"准备{mode} {len(files)} 个文件，共 {total_bytes / 1024 / 1024:.1f} MB")
    print(f"目标：oss://{args.bucket}/ ({args.endpoint})")

    uploaded = 0
    uploaded_bytes = 0

    def run_batch(batch: list[Path]) -> None:
        nonlocal uploaded, uploaded_bytes
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = [
                executor.submit(
                    upload_one,
                    path,
                    root,
                    args.bucket,
                    args.endpoint,
                    access_key_id,
                    access_key_secret,
                    args.dry_run,
                )
                for path in batch
            ]
            for future in concurrent.futures.as_completed(futures):
                key, size = future.result()
                uploaded += 1
                uploaded_bytes += size
                print(f"[{uploaded:>3}/{len(files)}] {key} ({size / 1024:.1f} KB)")

    try:
        run_batch(asset_files)
        run_batch(html_files)
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"完成：{uploaded} 个文件，{uploaded_bytes / 1024 / 1024:.1f} MB")
    if not args.dry_run:
        print(f"网站：{DEFAULT_SITE_URL}")
        print("说明：本次没有删除 OSS 中的任何旧文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
