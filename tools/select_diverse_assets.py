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
    "bird","eagle","hawk","falcon","owl","duck","goose","swan","peacock","parrot","macaw","penguin","puffin","ibis","crane","heron","egret","kingfisher","hoopoe","bee","bee-eater","bulbul","woodpecker","starling","sparrow","finch","tern",
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
    args = ap.parse_args()

    files = [f for f in os.listdir(args.dir) if not f.startswith('.')]
    files.sort()
    selected = []
    per = defaultdict(int)

    for f in files:
        if len(selected) >= args.limit:
            break
        key = animal_key_from_name(f)
        if per[key] >= args.per_animal_max:
            continue
        selected.append(f)
        per[key] += 1

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

