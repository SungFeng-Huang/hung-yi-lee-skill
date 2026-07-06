#!/usr/bin/env python3
"""Recommend candidate entries for graph_alignment.json.

Mines the built graph for concept pairs that LOOK like the same or closely
related concepts, so a human can decide merge vs align (the judgment call —
"is this a true synonym, or two things my taxonomy deliberately separates?" —
stays human; see graph_alignment.json's _comment).

Signals, strongest first:
  string   — normalized-equal labels (case/space/hyphen/plural), or one label
             is the acronym of the other's initials -> merge-leaning
  structure— high Jaccard overlap between the two concepts' DOCUMENT
             neighborhoods (videos + external docs that mention both), i.e.
             the co_mentioned INFERRED signal condensed per pair
             -> align-leaning (or merge if also string-similar)
  zh↔en    — one label CJK, one ASCII, with structural overlap: the classic
             cross-lingual gap (語音語言模型 vs Speech LLM) -> flagged

Reads wiki/graph/graph.local.json (falls back to graph.json). Excludes pairs
already covered by graph_alignment.json and skips god nodes (their neighbor
sets overlap with everything). Prints ready-to-paste JSON lines.

  python3 scripts/suggest_alignments.py [--top 25] [--min-shared 3]
      [--max-doc-degree 80] [--jaccard 0.35]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CJK = re.compile(r"[㐀-鿿]")


def norm_label(s: str) -> str:
    s = s.casefold()
    s = re.sub(r"[\s_\-]+", "", s)
    return s[:-1] if s.endswith("s") and len(s) > 3 else s


def acronym_of(short: str, long: str) -> bool:
    """`short` matches the initials of `long`'s words (GRPO ~ Group Relative
    Policy Optimization). Guarded against noise: the short side must be an
    ALL-CAPS token of >=3 letters (2-letter matches are overwhelmingly
    coincidental)."""
    if not re.fullmatch(r"[A-Z]{3,}", short):
        return False
    words = re.findall(r"[A-Za-z]+", long)
    if len(words) < 2:
        return False
    return short.casefold() == "".join(w[0] for w in words).casefold()


def load_covered(alignment_path: Path) -> set[frozenset[str]]:
    """Every pair already expressed by graph_alignment.json (merge or align),
    as casefolded label pairs."""
    covered: set[frozenset[str]] = set()
    try:
        data = json.loads(alignment_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return covered
    for group in list(data.get("merge", [])) + list(data.get("align", [])):
        for a, b in combinations(group, 2):
            covered.add(frozenset((a.casefold(), b.casefold())))
            covered.add(frozenset((norm_label(a), norm_label(b))))
    # `ignore` = human-reviewed-and-REJECTED pairs — suppressed exactly like
    # covered ones so the miner stops re-proposing them every rebuild.
    for pair in data.get("ignore", []):
        if len(pair) == 2:
            a, b = pair
            covered.add(frozenset((a.casefold(), b.casefold())))
            covered.add(frozenset((norm_label(a), norm_label(b))))
    return covered


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-shared", type=int, default=3,
                    help="minimum shared documents for a structural candidate")
    ap.add_argument("--jaccard", type=float, default=0.35,
                    help="minimum neighborhood Jaccard for a structural candidate")
    ap.add_argument("--max-doc-degree", type=int, default=80,
                    help="skip concepts mentioned by more documents than this "
                         "(god nodes overlap with everything)")
    args = ap.parse_args()

    graph_path = ROOT / "wiki" / "graph" / "graph.local.json"
    if not graph_path.exists():
        graph_path = ROOT / "wiki" / "graph" / "graph.json"
    g = json.loads(graph_path.read_text(encoding="utf-8"))
    print(f"[suggest-alignments] graph: {graph_path.name}")

    labels: dict[str, str] = {}
    for n in g["nodes"]:
        if n.get("type") == "concept":
            labels[n["id"]] = n.get("label") or n["id"]

    # Document neighborhoods: which videos/external docs mention each concept.
    docs: dict[str, set[str]] = defaultdict(set)
    for e in g["links"]:
        if e.get("relation") != "mentions":
            continue
        s, t = e["source"], e["target"]
        if t in labels and (s.startswith("video_") or s.startswith("external_")):
            docs[t].add(s)
        elif s in labels and (t.startswith("video_") or t.startswith("external_")):
            docs[s].add(t)

    covered = load_covered(ROOT / "scripts" / "graph_alignment.json")
    # Alt labels of already-merged nodes count as covered too: the display
    # label carries "（=a/b）" — strip that part for comparison.
    def display(cid: str) -> str:
        # strip the merged-node alt-label suffix, tolerant of ASCII parens
        # and trailing whitespace: 「DPO（=a/b）」 / "DPO (=a/b)"
        return re.sub(r"\s*[（(]=.*?[）)]\s*$", "", labels[cid]).strip()

    def alt_labels(cid: str) -> list[str]:
        m = re.search(r"[（(]=(.*?)[）)]\s*$", labels[cid])
        return m.group(1).split("/") if m else []

    cands = []
    ids = [c for c in labels if len(docs[c]) <= args.max_doc_degree]
    skipped_gods = len(labels) - len(ids)
    for a, b in combinations(sorted(ids), 2):
        la, lb = display(a), display(b)
        pair_forms = {frozenset((la.casefold(), lb.casefold())),
                      frozenset((norm_label(la), norm_label(lb)))}
        # a pair is also covered when ANY alt label of one side pairs with the
        # other (the table already relates them through the merged node)
        for x in [la] + alt_labels(a):
            for y in [lb] + alt_labels(b):
                pair_forms.add(frozenset((x.casefold(), y.casefold())))
        if pair_forms & covered:
            continue
        shared = docs[a] & docs[b]
        union = docs[a] | docs[b]
        jac = len(shared) / len(union) if union else 0.0
        string_hit = (norm_label(la) == norm_label(lb)
                      or acronym_of(la, lb) or acronym_of(lb, la))
        struct_hit = len(shared) >= args.min_shared and jac >= args.jaccard
        if not string_hit and not struct_hit:
            continue
        crossling = bool(CJK.search(la)) != bool(CJK.search(lb))
        # merge-leaning when the NAMES look like the same thing; otherwise the
        # structure says "related" -> align-leaning. Human decides.
        kind = "merge?" if string_hit else "align?"
        score = (2.0 if string_hit else 0.0) + jac + min(len(shared), 10) / 10.0
        cands.append((score, kind, la, lb, len(shared), jac, crossling))

    cands.sort(reverse=True)
    if not cands:
        print("no candidates above thresholds — try lowering --jaccard/--min-shared")
        return 0
    print(f"{len(cands)} candidates (showing top {args.top}; "
          f"{skipped_gods} god nodes skipped at doc-degree>{args.max_doc_degree})\n")
    print(f"{'':2}{'kind':7} {'shared':>6} {'jac':>5}  pair")
    for score, kind, la, lb, sh, jac, xl in cands[: args.top]:
        mark = " zh↔en" if xl else ""
        print(f"  {kind:7} {sh:6d} {jac:5.2f}  {la}  ⇄  {lb}{mark}")
    print("\nready-to-paste JSON rows (verify merge vs align by YOUR taxonomy first):")
    for score, kind, la, lb, sh, jac, xl in cands[: args.top]:
        key = "merge" if kind == "merge?" else "align"
        print(f"  {key}: {json.dumps([la, lb], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
