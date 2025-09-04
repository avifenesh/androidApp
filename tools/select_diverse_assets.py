#!/usr/bin/env python3
"""
Select a diverse subset of images from an assets folder by limiting the number
per animal keyword, to reduce repetition. Removes non-selected files if
--prune is passed.

Example:
  python tools/select_diverse_assets.py \
      --dir app/src/main/assets/animals \
      --limit 80 \
      --per-animal-max 3 \
      --prune
"""
import argparse
import os
import re
from collections import defaultdict

ANIMAL_TOKENS = {
    # Pets / farm
    "cat","kitten","dog","puppy","cow","cattle","bull","calf","yak","ox","buffalo","water","goat","sheep","ram","ewe","pig","boar","hog","horse","pony","donkey","mule","llama","alpaca","camel",
    # Big cats & canids
    "lion","tiger","leopard","cheetah","jaguar","panther","lynx","puma","cougar","bobcat","fox","wolf","jackal","dingo",
    # Bears
    "bear","panda","koala",
    # Primates
    "monkey","baboon","mandrill","gorilla","chimp","chimpanzee","orangutan","lemur",
    # Hooved animals
    "zebra","giraffe","elephant","rhino","rhinoceros","hippo","hippopotamus","deer","elk","moose","ibex","tahr","chamois","antelope","gazelle","gnu","wildebeest","pronghorn","oryx","addax","kob","topi","kudu","bongo","sable","roan","hartebeest","springbok",
    # Others
    "kangaroo","wallaby","badger","otter","raccoon","skunk","hyena","weasel","marten","beaver","hare","rabbit","capybara",
    # Birds (optional present in set)
    "bird","eagle","hawk","falcon","owl","duck","goose","swan","peacock","parrot","macaw","penguin","puffin","ibis","crane","heron","egret","kingfisher","hoopoe","bulbul","woodpecker","starling","sparrow","finch","tern",
}

STOPWORDS = {
    "the","and","or","of","in","on","with","at","to","from","by","for","near","under","over","between","around",
    "male","female","adult","juvenile","young","baby","close","closeup","close-up","head","portrait","nature","wildlife",
    "national","park","reserve","forest","zoo","sanctuary","lake","river","mountain","valley","island","beach","desert",
    "golden","hour","sunset","sunrise","night","day","sky","clouds","grass","tree","flowers","garden",
    "photo","photograph","picture","image","edit","cropped","crop","version","final","copy",
    "jpg","jpeg","png","gif","tif","tiff",
}

TOKEN_SPLIT = re.compile(r"[^a-zA-Z]+")


def animal_key_from_name(name: str) -> str:
    base = os.path.splitext(os.path.basename(name))[0].lower()
    tokens = [t for t in TOKEN_SPLIT.split(base) if t]
    tokens = [t for t in tokens if t not in STOPWORDS]
    # Prefer tokens appearing in ANIMAL_TOKENS; fall back to first non-stopword token
    for t in tokens:
        if t in ANIMAL_TOKENS:
            return t
    return tokens[0] if tokens else base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Assets directory containing images")
    ap.add_argument("--limit", type=int, default=80, help="Max total images to keep")
    ap.add_argument("--per-animal-max", type=int, default=3, help="Max images per animal key")
    ap.add_argument("--prune", action="store_true", help="Delete non-selected files")
    ap.add_argument("--quota", default="", help="Comma-separated quotas like lion=2,tiger=2,parrot=2")
    ap.add_argument("--ensure", default="", help="Comma-separated tokens to ensure at least 1 if available (e.g., leopard,elephant,buffalo,cheetah,wilddog)")
    ap.add_argument("--birds-min", type=int, default=0, help="Ensure at least this many bird images if available")
    args = ap.parse_args()

    files = [f for f in os.listdir(args.dir) if not f.startswith('.')]
    files.sort()
    selected: list[str] = []
    per: dict[str,int] = defaultdict(int)

    # Synonyms mapping to canonical tokens
    synonyms = {
        "giraff": "giraffe",
        "giraffes": "giraffe",
        "zebras": "zebra",
        "rinors": "rhino",
        "rino": "rhino",
        "rhinoceros": "rhino",
        "rhinoceroses": "rhino",
        "parots": "parrot",
        "parrots": "parrot",
        "monkeys": "monkey",
        "lions": "lion",
        "tigers": "tiger",
        "cows": "cow",
        "snakes": "snake",
        "wild": "wilddog",  # heuristic for African wild dog filenames
        "dog": "wilddog"     # careful: maps generic dog to wilddog only for ensure/quota parsing
    }

    def canon(tok: str) -> str:
        t = tok.strip().lower()
        return synonyms.get(t, t)

    # Parse quotas map
    quotas: dict[str,int] = {}
    if args.quota.strip():
        for pair in args.quota.split(','):
            if not pair.strip():
                continue
            if '=' in pair:
                k, v = pair.split('=', 1)
                try:
                    quotas[canon(k)] = max(0, int(v))
                except ValueError:
                    continue

    ensure_tokens = [canon(t) for t in args.ensure.split(',') if t.strip()]

    # Precompute keys for files
    file_keys = [(f, animal_key_from_name(f)) for f in files]

    # 1) Satisfy explicit quotas first
    if quotas:
        for want_key, want_n in quotas.items():
            if want_n <= 0:
                continue
            for f, k in file_keys:
                if len(selected) >= args.limit:
                    break
                if per.get(k, 0) >= args.per_animal_max:
                    continue
                if k == want_key and f not in selected:
                    selected.append(f)
                    per[k] = per.get(k, 0) + 1
                    if per[k] >= want_n:
                        break

    # 2) Ensure certain tokens at least once
    for tok in ensure_tokens:
        if len(selected) >= args.limit:
            break
        if per.get(tok, 0) > 0:
            continue
        for f, k in file_keys:
            if k == tok and f not in selected:
                selected.append(f)
                per[k] = per.get(k, 0) + 1
                break

    # Helper to check bird tokens
    bird_tokens = {"bird","eagle","hawk","falcon","owl","duck","goose","swan","peacock","parrot","macaw","penguin","puffin","ibis","crane","heron","egret","kingfisher","hoopoe","bulbul","woodpecker","starling","sparrow","finch","tern"}

    # 3) Fill to birds-min with bird images
    if args.birds_min > 0:
        for f, k in file_keys:
            if len(selected) >= args.limit:
                break
            if len([1 for s in selected if animal_key_from_name(s) in bird_tokens]) >= args.birds_min:
                break
            if k in bird_tokens and per.get(k, 0) < args.per_animal_max and f not in selected:
                selected.append(f)
                per[k] = per.get(k, 0) + 1

    # 4) Fill the rest up to limit with diverse items respecting per-animal-max
    for f, k in file_keys:
        if len(selected) >= args.limit:
            break
        if per.get(k, 0) >= args.per_animal_max:
            continue
        if f in selected:
            continue
        selected.append(f)
        per[k] = per.get(k, 0) + 1

    if args.prune:
        keep = set(selected)
        removed = 0
        for f in files:
            if f not in keep:
                try:
                    os.remove(os.path.join(args.dir, f))
                    removed += 1
                except Exception:
                    pass
        print(f"Kept {len(selected)} files, removed {removed} others.")
    else:
        print(f"Would keep {len(selected)} files (not pruning).")
    print("Per-animal counts:")
    for k in sorted(per.keys()):
        print(f"  {k}: {per[k]}")

if __name__ == "__main__":
    main()
