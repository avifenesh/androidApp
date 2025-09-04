#!/usr/bin/env python3
"""
Scrape Creative Commons animal images from Wikimedia Commons categories.

Usage examples:
  # Single category
  python tools/scrape_wikimedia_animals.py \
      --category "Category:Featured pictures of mammals" \
      --limit 150 \
      --out app/src/main/assets/animals

  # Multiple categories with keyword filters
  python tools/scrape_wikimedia_animals.py \
      --category "Category:Featured pictures of mammals" \
      --category "Category:Featured pictures of birds" \
      --include "cat,dog,elephant,giraffe,zebra,lion,tiger,bear,horse,cow,goat,sheep,fox,monkey,panda,koala,bird,parrot,peacock,penguin" \
      --exclude "jellyfish,coral,anemone,urchin,starfish,octopus,squid,shrimp,crab,sponge,cnidaria,ctenophora,fish,marine,sea,worm,spider,mite,tick,insect,mosquito" \
      --exclude-ext ".svg" \
      --limit 300 \
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
    ap.add_argument("--category", action="append", required=True, help="Wikimedia Commons category; repeatable")
    ap.add_argument("--out", required=True, help="Output folder for images")
    ap.add_argument("--limit", type=int, default=50, help="Max number of images")
    ap.add_argument("--include", default="", help="Comma-separated keywords to prefer (optional)")
    ap.add_argument("--exclude", default="", help="Comma-separated keywords to skip")
    ap.add_argument("--exclude-ext", default=".svg", help="Comma-separated file extensions to skip (e.g., .svg,.tif)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    meta_path = os.path.join(os.path.dirname(args.out.rstrip("/")), "animals_metadata.csv")
    include_kw = [s.strip().lower() for s in args.include.split(",") if s.strip()]
    exclude_kw = [s.strip().lower() for s in args.exclude.split(",") if s.strip()]
    exclude_ext = [s.strip().lower() for s in args.exclude_ext.split(",") if s.strip()]

    # Gather files from all categories up to limit
    titles: list[str] = []
    for cat in args.category:
        remaining = args.limit - len(titles)
        if remaining <= 0:
            break
        files = fetch_category_files_recursive(cat, remaining)
        titles.extend([m["title"] for m in files])
    titles = list(dict.fromkeys(titles))  # de-dup while preserving order
    if not titles:
        print("No images found for:", ", ".join(args.category))
        return
    info = fetch_image_info(titles)

    with open(meta_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "source_url", "license", "artist", "credit"])
        downloaded = 0
        kept = 0
        for title, ii in info.items():
            url = ii.get("url")
            width = ii.get("width", 0)
            height = ii.get("height", 0)
            if not url or (width < 640 and height < 640):
                continue
            base = sanitize_filename(os.path.basename(url))
            # Extension filter
            if any(base.lower().endswith(ext) for ext in exclude_ext):
                continue
            # Keyword filters on filename and title
            title_l = (title or "").lower() + " " + base.lower()
            if exclude_kw and any(k in title_l for k in exclude_kw):
                continue
            if include_kw and not any(k in title_l for k in include_kw):
                # If include list provided, skip non-matching
                continue
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
                kept += 1
                print(f"Saved {base}")
            except Exception as e:
                print("Failed ", url, e)
        print(f"Downloaded {downloaded} images to {args.out}; kept {kept} after filters")

if __name__ == "__main__":
    main()
