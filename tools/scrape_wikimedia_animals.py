#!/usr/bin/env python3
"""
Scrape Creative Commons animal images from Wikimedia Commons categories.

Usage:
  python tools/scrape_wikimedia_animals.py \
      --category "Category:Animal portraits" \
      --limit 50 \
      --out app/src/main/assets/animals

Notes:
  - Ensure licenses are appropriate; this script stores metadata in a CSV next to images.
  - Running this requires network access.
"""
import argparse
import csv
import os
import re
import sys
import time
from typing import Dict, List

import json
try:
    import requests
except Exception:
    print("This script requires the 'requests' package.")
    sys.exit(1)

API = "https://commons.wikimedia.org/w/api.php"
UA = {
    "User-Agent": "KidAnimalsApp/1.0 (educational use)"
}


def fetch_category_members(category: str, cmtype: str, limit: int, cmcontinue: str | None = None) -> tuple[list[dict], str | None]:
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmtype": cmtype,
        "cmlimit": min(50, limit),
        "format": "json",
        "origin": "*",
    }
    if cmcontinue:
        params["cmcontinue"] = cmcontinue
    r = requests.get(API, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    data = r.json()
    members = data.get("query", {}).get("categorymembers", [])
    next_cont = data.get("continue", {}).get("cmcontinue")
    return members, next_cont


def fetch_category_files_recursive(category: str, limit: int, max_depth: int = 3) -> List[Dict]:
    files: List[Dict] = []
    visited: set[str] = set()

    def walk(cat: str, depth: int):
        nonlocal files
        if depth > max_depth or len(files) >= limit or cat in visited:
            return
        visited.add(cat)
        cont = None
        while len(files) < limit:
            members, cont = fetch_category_members(cat, cmtype="file|subcat", limit=limit - len(files), cmcontinue=cont)
            for m in members:
                title: str = m.get("title", "")
                if title.startswith("File:"):
                    files.append(m)
                    if len(files) >= limit:
                        break
                elif title.startswith("Category:"):
                    walk(title, depth + 1)
                    if len(files) >= limit:
                        break
            if not cont or len(files) >= limit:
                break
        time.sleep(0.1)

    walk(category, 0)
    return files[:limit]


def fetch_image_info(titles: List[str]) -> Dict[str, Dict]:
    info: Dict[str, Dict] = {}
    for i in range(0, len(titles), 50):
        batch = titles[i : i + 50]
        params = {
            "action": "query",
            "prop": "imageinfo",
            "titles": "|".join(batch),
            "iiprop": "url|extmetadata|size",
            "format": "json",
            "origin": "*",
        }
        r = requests.get(API, params=params, headers=UA, timeout=30)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            title = p.get("title")
            ii = (p.get("imageinfo") or [None])[0]
            if title and ii:
                info[title] = ii
        time.sleep(0.2)
    return info


def sanitize_filename(name: str) -> str:
    name = name.replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9_.-]", "", name)
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, help="Wikimedia Commons category (e.g., 'Category:Animal portraits')")
    ap.add_argument("--out", required=True, help="Output folder for images")
    ap.add_argument("--limit", type=int, default=50, help="Max number of images")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    meta_path = os.path.join(os.path.dirname(args.out.rstrip("/")), "animals_metadata.csv")
    titles = [m["title"] for m in fetch_category_files_recursive(args.category, args.limit)]
    if not titles:
        print("No images found for:", args.category)
        return
    info = fetch_image_info(titles)

    with open(meta_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "source_url", "license", "artist", "credit"])
        downloaded = 0
        for title, ii in info.items():
            url = ii.get("url")
            width = ii.get("width", 0)
            height = ii.get("height", 0)
            if not url or (width < 640 and height < 640):
                continue
            base = sanitize_filename(os.path.basename(url))
            out_path = os.path.join(args.out, base)
            try:
                r = requests.get(url, headers=UA, timeout=60)
                r.raise_for_status()
                with open(out_path, "wb") as imgf:
                    imgf.write(r.content)
                meta = ii.get("extmetadata", {})
                license_short = (meta.get("LicenseShortName", {}).get("value") or "").strip()
                artist = (meta.get("Artist", {}).get("value") or "").strip()
                credit = (meta.get("Credit", {}).get("value") or "").strip()
                writer.writerow([base, url, license_short, artist, credit])
                downloaded += 1
                print(f"Saved {base}")
            except Exception as e:
                print("Failed ", url, e)
        print(f"Downloaded {downloaded} images to {args.out}")

if __name__ == "__main__":
    main()
