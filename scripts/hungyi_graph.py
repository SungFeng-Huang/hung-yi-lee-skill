#!/usr/bin/env python3
"""
Knowledge graph builder for the Hung-Yi Lee skill.

Inspired by Graphify (https://github.com/safishamsi/graphify):
- Extracts concept nodes and relationship edges from transcripts, topics, and references.
- Builds a persistent NetworkX graph with Louvain community detection.
- Generates GRAPH_REPORT.md, graph.json, and graph.html outputs.

All edges are tagged EXTRACTED, INFERRED, or AMBIGUOUS following Graphify's audit convention.
"""

from __future__ import annotations

import html
import json
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONCEPT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("english_term", re.compile(r"\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+)\b")),
    ("tech_term", re.compile(
        r"\b((?:self-supervised|pre-?train|fine-?tun|back-?prop|over-?fit|under-?fit|"
        r"cross-?entropy|multi-?head|auto-?regressive|flow-?matching|"
        r"[A-Z][a-zA-Z]*(?:-[A-Za-z]+)+)(?:ing|ed|tion|ment|s)?)\b",
        re.IGNORECASE,
    )),
    ("model_name", re.compile(
        r"\b(GPT-?[0-9o]*|BERT|RoBERTa|T5|LLaMA|Llama|Qwen|DeepSeek(?:-R1)?|"
        r"Claude|Gemini|Gemma|Mistral|Whisper|HuBERT|wav2vec|WavLM|"
        r"Transformer|SUPERB|SoundStream|EnCodec|DAC|SpeechTokenizer|"
        r"Moshi|VoiceCraft|SwinTransformer|ViT|DALL-?E|Diffusion|"
        r"FlashAttention|RoPE|LoRA|DPO|RLHF|SFT|PPO|GRPO|"
        r"GAN|VAE|Flow|Codec|Tokenizer)\b",
        re.IGNORECASE,
    )),
    ("zh_concept", re.compile(
        r"(語言模型|語音模型|注意力機制|自監督學習|遷移學習|強化學習|"
        r"對抗式生成|擴散模型|生成模型|殘差網路|卷積神經網路|"
        r"損失函數|梯度下降|反向傳播|過擬合|正則化|"
        r"上下文工程|機器學習|深度學習|自然語言處理|"
        r"語音辨識|語音合成|語音分離|語音轉換|語音生成|全雙工|語音語言模型|"
        r"模型編輯|模型合併|終身學習|"
        r"推理|評估|基準測試|解剖|可解釋性)"
    )),
    # Whitelisted bare acronyms. english_term needs TWO capitalized words, so
    # ubiquitous speech acronyms never became nodes on their own. UPPERCASE
    # only (no IGNORECASE) — "tts"/"asr" in prose or code snippets stay out.
    # Bare VC is deliberately absent: in ML lectures it collides with
    # VC dimension / VC++ / venture capital (the "Voice Conversion" full form
    # still merge-folds onto 語音轉換 via graph_alignment.json).
    ("acronym", re.compile(r"\b(TTS|ASR|SVS|S2ST|LALM)\b")),
]

# Concepts that are too generic to be useful as nodes
STOP_CONCEPTS = {
    "The", "This", "That", "What", "How", "When", "Where",
    "New", "Old", "Good", "Bad", "More", "Less",
    "Part", "Step", "Note", "Example", "Section",
    "Today", "Course", "Lecture", "Video",
}

# Minimum frequency for a concept to become a node (across all documents)
MIN_CONCEPT_FREQUENCY = 2

# ---------------------------------------------------------------------------
# Concept alignment (scripts/graph_alignment.json)
# ---------------------------------------------------------------------------
# Two relations, two mechanisms:
#   merge: TRUE synonyms — every variant maps onto the canonical label (first
#          list entry) BEFORE node ids are formed, so all surface forms share
#          one node (labels compared casefold; canonical keeps its casing).
#   align: related-but-deliberately-DISTINCT concepts — an `aligned_with`
#          edge (confidence ALIGNED) is added between existing nodes, never a
#          merge (e.g. a taxonomy that separates 語音合成 from the broader
#          語音生成 family must survive alignment).

ALIGNMENT_PATH = Path(__file__).resolve().parent / "graph_alignment.json"
ROOT_DIR = Path(__file__).resolve().parent.parent


def _rel(path) -> str:
    """source_file as a REPO-RELATIVE path. Two reasons: portability (the
    graph outputs are tracked — absolute paths break on any other machine)
    and sanitization (an absolute path embeds the local username/home in
    published files). Paths outside the repo fall back unchanged."""
    try:
        return str(Path(path).resolve().relative_to(ROOT_DIR))
    except (ValueError, OSError):
        return str(path)


def load_alignment(path: Path = ALIGNMENT_PATH) -> dict:
    """Parse the alignment table. Missing file -> empty alignment; malformed
    file or a variant claimed by two merge groups -> ValueError (silent
    misalignment would corrupt node identity)."""
    empty = {"canonical": {}, "alt_labels": {}, "align": []}
    if not path.exists():
        return empty
    data = json.loads(path.read_text(encoding="utf-8"))
    stop_cf = {s.casefold() for s in STOP_CONCEPTS}
    canonical: dict[str, str] = {}
    alt_labels: dict[str, list[str]] = {}
    for group in data.get("merge", []):
        if (not isinstance(group, list) or len(group) < 2
                or not all(isinstance(x, str) and x.strip() for x in group)):
            raise ValueError(f"{path}: merge groups must be lists of >=2 non-empty strings: {group!r}")
        canon = group[0].strip()
        if canon in alt_labels:
            # A second group with the same canonical would silently REPLACE
            # the first group's alt_labels (dropping its query aliases).
            raise ValueError(f"{path}: canonical {canon!r} declared by two merge groups "
                             f"— put all variants in one group")
        for variant in group:
            key = re.sub(r"\s+", " ", variant.strip()).casefold()
            if key in stop_cf:
                # A stop word as variant would launder stop surfaces into the
                # graph; as canonical it would drop every variant instead.
                raise ValueError(f"{path}: {variant!r} is a STOP_CONCEPT — remove it")
            if key in canonical and canonical[key] != canon:
                raise ValueError(f"{path}: {variant!r} appears in two merge groups "
                                 f"({canonical[key]!r} vs {canon!r})")
            canonical[key] = canon
        alt_labels[canon] = [v.strip() for v in group[1:]]
    align = []
    for group in data.get("align", []):
        if (not isinstance(group, list) or len(group) < 2
                or not all(isinstance(x, str) and x.strip() for x in group)):
            raise ValueError(f"{path}: align groups must be lists of >=2 non-empty strings: {group!r}")
        entries = [x.strip() for x in group]
        if any(e.casefold() in stop_cf for e in entries):
            raise ValueError(f"{path}: align group {group!r} contains a STOP_CONCEPT")
        # Entries that merge-fold onto one canonical would collapse to the
        # same node id and the edge would be silently skipped — misplaced
        # entries belong in the merge table instead.
        folded = {canonical.get(re.sub(r"\s+", " ", e).casefold(), e) for e in entries}
        if len(folded) < 2:
            raise ValueError(f"{path}: align group {group!r} collapses to a single "
                             f"merged concept — it belongs in 'merge'")
        align.append(entries)
    return {"canonical": canonical, "alt_labels": alt_labels, "align": align}


_ALIGNMENT = load_alignment()

# ---------------------------------------------------------------------------
# Concept extraction
# ---------------------------------------------------------------------------


def normalize_concept(raw: str) -> str:
    """Normalize a concept string for deduplication, then fold merge-variants
    onto their canonical label (see graph_alignment.json) — this is the ONE
    choke point every extractor goes through, so lecture and external corpora
    can't fork the same concept into differently-spelled nodes."""
    normalized = raw.strip()
    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    return _ALIGNMENT["canonical"].get(normalized.casefold(), normalized)


def slug(text: str) -> str:
    """Node-id-safe slug that PRESERVES CJK. The old inline pattern
    (`[^a-zA-Z0-9_]` -> `_`) mapped every CJK char to `_`, so distinct
    Chinese concepts of the same length collapsed into ONE node id
    (e.g. 語音合成 and 語音辨識 both -> `concept_____`). Keep ASCII alnum
    plus kana (U+3040-30FF), 〇, CJK Ext-A, the basic ideographs, and the
    compatibility ideographs; collapse everything else to single
    underscores (this also normalizes ASCII runs — `a  (b)` -> `a_b` —
    which is an id CHANGE vs the old per-char mapping; safe because the
    graph is fully rebuilt from source on every `graph build` and node
    ids are never persisted across builds)."""
    lowered = text.lower()
    out = re.sub(
        r"[^a-z0-9぀-ヿ〇㐀-䶿一-鿿豈-﫿]+",
        "_", lowered)
    return out.strip("_") or "_"


def extract_concepts_from_text(text: str) -> list[dict]:
    """Extract concept mentions from a text block."""
    found: list[dict] = []
    for pattern_name, pattern in CONCEPT_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1) if match.lastindex else match.group(0)
            normalized = normalize_concept(raw)
            if normalized in STOP_CONCEPTS or len(normalized) < 2:
                continue
            found.append({
                "raw": normalized,
                "pattern": pattern_name,
                "start": match.start(),
            })
    return found


def extract_from_transcript(path: Path) -> dict:
    """Extract nodes and edges from a transcript markdown file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Parse YAML frontmatter
    meta: dict[str, Any] = {}
    if lines and lines[0].strip() == "---":
        end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end = i
                break
        if end:
            for line in lines[1:end]:
                if ":" in line:
                    key, _, val = line.partition(":")
                    meta[key.strip()] = val.strip().strip('"').strip("'")

    video_id = meta.get("video_id", path.stem)
    title = meta.get("title", path.stem)
    series = meta.get("series", "")
    topics_raw = meta.get("topics", "[]")
    try:
        topics = json.loads(topics_raw) if topics_raw.startswith("[") else [topics_raw]
    except json.JSONDecodeError:
        topics = []

    # Extract transcript lines
    transcript_lines = []
    for line in lines:
        if line.startswith("- ["):
            # Extract text after timestamp
            m = re.match(r"^- \[\d{2}:\d{2}:\d{2}\]\s*(.*)$", line)
            if m:
                transcript_lines.append(m.group(1))

    full_text = title + "\n" + "\n".join(transcript_lines)

    # Extract concepts from the full text
    concepts = extract_concepts_from_text(full_text)
    concept_counts: Counter = Counter()
    for c in concepts:
        concept_counts[c["raw"]] += 1

    nodes: list[dict] = []
    edges: list[dict] = []

    # Video node
    video_node_id = f"video_{video_id}"
    nodes.append({
        "id": video_node_id,
        "label": title,
        "type": "video",
        "source_file": _rel(path),
        "video_id": video_id,
        "series": series,
        "topics": topics,
    })

    # Concept nodes + edges to video
    for concept_text, count in concept_counts.items():
        concept_id = f"concept_{slug(concept_text)}"
        nodes.append({
            "id": concept_id,
            "label": concept_text,
            "type": "concept",
            "source_file": _rel(path),
            "mention_count": count,
        })
        edges.append({
            "source": video_node_id,
            "target": concept_id,
            "relation": "mentions",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": min(count / 5.0, 3.0),  # Normalize weight
            "source_file": _rel(path),
        })

    # Series edge
    if series:
        series_id = f"series_{slug(series)}"
        nodes.append({
            "id": series_id,
            "label": series,
            "type": "series",
            "source_file": _rel(path),
        })
        edges.append({
            "source": video_node_id,
            "target": series_id,
            "relation": "belongs_to_series",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": 1.0,
            "source_file": _rel(path),
        })

    # Topic edges
    for topic in topics:
        topic_id = f"topic_{topic}"
        nodes.append({
            "id": topic_id,
            "label": topic.replace("-", " ").title(),
            "type": "topic",
            "source_file": _rel(path),
        })
        edges.append({
            "source": video_node_id,
            "target": topic_id,
            "relation": "covers_topic",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": 1.5,
            "source_file": _rel(path),
        })

    return {"nodes": nodes, "edges": edges}


def extract_from_metadata(video: dict) -> dict:
    """Extract lightweight nodes/edges from a video that has no transcript."""
    video_id = video["video_id"]
    title = video["title"]
    series = video.get("series", "")
    topics = video.get("topics", [])

    nodes: list[dict] = []
    edges: list[dict] = []

    video_node_id = f"video_{video_id}"
    nodes.append({
        "id": video_node_id,
        "label": title,
        "type": "video",
        "source_file": None,
        "video_id": video_id,
        "series": series,
        "topics": topics,
        "metadata_only": True,
    })

    # Title-based concept extraction (lighter)
    concepts = extract_concepts_from_text(title)
    concept_counts: Counter = Counter()
    for c in concepts:
        concept_counts[c["raw"]] += 1

    for concept_text, count in concept_counts.items():
        concept_id = f"concept_{slug(concept_text)}"
        nodes.append({
            "id": concept_id,
            "label": concept_text,
            "type": "concept",
            "source_file": None,
            "mention_count": count,
        })
        edges.append({
            "source": video_node_id,
            "target": concept_id,
            "relation": "mentions",
            "confidence": "INFERRED",
            "confidence_score": 0.6,
            "weight": 0.5,
            "source_file": None,
        })

    if series:
        series_id = f"series_{slug(series)}"
        nodes.append({
            "id": series_id,
            "label": series,
            "type": "series",
            "source_file": None,
        })
        edges.append({
            "source": video_node_id,
            "target": series_id,
            "relation": "belongs_to_series",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": 1.0,
            "source_file": None,
        })

    for topic in topics:
        topic_id = f"topic_{topic}"
        nodes.append({
            "id": topic_id,
            "label": topic.replace("-", " ").title(),
            "type": "topic",
            "source_file": None,
        })
        edges.append({
            "source": video_node_id,
            "target": topic_id,
            "relation": "covers_topic",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": 1.0,
            "source_file": None,
        })

    return {"nodes": nodes, "edges": edges}


def extract_from_wiki_topic(path: Path) -> dict:
    """Extract nodes from a wiki topic page."""
    text = path.read_text(encoding="utf-8")
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    label = first_line.lstrip("# ").strip() if first_line.startswith("#") else path.stem

    topic_id = f"topic_{path.stem}"
    nodes = [{"id": topic_id, "label": label, "type": "topic", "source_file": _rel(path)}]
    edges: list[dict] = []

    # Extract concepts from the topic page
    concepts = extract_concepts_from_text(text)
    concept_counts: Counter = Counter()
    for c in concepts:
        concept_counts[c["raw"]] += 1

    for concept_text, count in concept_counts.most_common(15):
        concept_id = f"concept_{slug(concept_text)}"
        nodes.append({
            "id": concept_id,
            "label": concept_text,
            "type": "concept",
            "source_file": _rel(path),
            "mention_count": count,
        })
        edges.append({
            "source": topic_id,
            "target": concept_id,
            "relation": "contains_concept",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": 1.0,
            "source_file": _rel(path),
        })

    return {"nodes": nodes, "edges": edges}


def extract_from_external(path: Path) -> dict:
    """Extract concepts from an external-corpus document.

    External corpora live under `raw/external/<collection>/*.md` (gitignored —
    personal/third-party content, e.g. the user's own note cards). Frontmatter
    contract: `title` and `source_type` required, `collection` defaults to the
    parent directory name; `url` / `origin_id` optional. Nodes get
    type="external" plus source_type/collection attrs so downstream consumers
    (query output, prompts) can frame them honestly as NON-lecture sources —
    never as something the teacher said."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    meta: dict[str, str] = {}
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                body_start = i + 1
                break
            if line.lstrip().startswith("- "):
                # YAML block-list syntax — the contract is single-line
                # values ("a,b,c"); a silent miss here would drop links/
                # model_names AND disable the aggregator gate downstream.
                raise ValueError(f"{path}: frontmatter uses a YAML list — "
                                 f"use a single-line quoted CSV value instead")
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"').strip("'")
        if body_start == 0:
            # Unclosed frontmatter would silently swallow the whole body as
            # metadata — fail fast with the offending file.
            raise ValueError(f"{path}: unclosed frontmatter (missing second '---')")

    # Contract: title + source_type are REQUIRED (the docs promise consumers
    # can trust provenance); a fallback here would silently weaken that.
    if not meta.get("title") or not meta.get("source_type"):
        raise ValueError(f"{path}: external corpus doc needs frontmatter with "
                         f"'title' and 'source_type'")
    title = meta["title"]
    source_type = meta["source_type"]
    collection = meta.get("collection") or path.parent.name
    body = "\n".join(lines[body_start:])

    ext_id = f"external_{slug(collection)}_{slug(meta.get('origin_id') or path.stem)}"
    node: dict[str, Any] = {
        "id": ext_id,
        "label": title,
        "type": "external",
        "source_type": source_type,
        "collection": collection,
        "source_file": _rel(path),
    }
    if meta.get("url"):
        node["url"] = meta["url"]
    if meta.get("origin_id"):
        node["origin_id"] = meta["origin_id"]
    # `links:` = comma-separated origin_ids of other external docs this card
    # links to (exporter-provided). Held in a PRIVATE key: build_graph pops it
    # into EXTRACTED links_to edges; it never enters the final node attrs.
    if meta.get("links"):
        node["_links"] = [x.strip() for x in meta["links"].split(",") if x.strip()]
    nodes = [node]
    edges: list[dict] = []

    concepts = extract_concepts_from_text(title + "\n" + body)
    concept_counts: Counter = Counter()
    for c in concepts:
        concept_counts[c["raw"]] += 1

    # Model-name signals for `describes` edges (private key, popped in
    # build_graph — never enters final node attrs). Priority:
    #   1) frontmatter `model_names:` (exporter-curated short names — covers
    #      papers whose TITLE omits the model, e.g. "Language Models are
    #      Few-Shot Learners" = GPT-3)                       -> EXTRACTED
    #   2) fallback: the doc's DOMINANT self-mentioned model concept — top-1
    #      model_name/acronym concept with >=3 mentions AND >=2x the runner-
    #      up. Papers self-mention their own model overwhelmingly; survey/
    #      comparison docs list many models with no dominant one, so the
    #      dominance gate keeps them out                     -> INFERRED
    #   3) title-before-colon short name, ONLY when the body extractions
    #      also produced that concept (never a signal on its own)
    # Heuristic signals (2/3) are skipped for AGGREGATOR docs — anything
    # carrying >=3 `links:` targets is a curator/overview document whose
    # dominant model name is its NARRATIVE subject, not its identity (a hub
    # centred on one model would otherwise pass any frequency gate).
    model_names: list[list[str]] = []
    if meta.get("model_names"):
        model_names = [[x.strip(), "frontmatter"]
                       for x in meta["model_names"].split(",") if x.strip()]
    elif meta.get("aggregator", "").lower() in ("true", "yes", "1") \
            or len(node.get("_links") or []) >= 3:
        # declared aggregator (frontmatter) or structurally link-heavy:
        # skip the heuristic signals entirely.
        pass
    else:
        # body-only counts: the title must not push a name over the dominance
        # gate, nor satisfy its own title-assist condition.
        body_concepts = extract_concepts_from_text(body)
        body_counts: Counter = Counter(c["raw"] for c in body_concepts)
        modelish = {c["raw"] for c in body_concepts
                    if c["pattern"] in ("model_name", "acronym")}
        cands = sorted(((body_counts[r], r) for r in modelish), reverse=True)
        if cands and cands[0][0] >= 3 and \
                cands[0][0] >= 2 * (cands[1][0] if len(cands) > 1 else 1):
            model_names = [[cands[0][1], "self-mention"]]
        m = re.match(r"^(?:\[[^\]]+\]\s*)?([^:：]{2,60})[:：]", title)
        if m:
            short = normalize_concept(m.group(1))
            if short in body_counts and short not in [n for n, _ in model_names]:
                model_names.append([short, "title"])
    if model_names:
        node["_model_names"] = model_names

    # External docs can be much longer than references/* — cap a bit higher
    # so a comparison card's core vocabulary still makes it into the graph.
    for concept_text, count in concept_counts.most_common(40):
        concept_id = f"concept_{slug(concept_text)}"
        nodes.append({
            "id": concept_id,
            "label": concept_text,
            "type": "concept",
            "source_file": _rel(path),
            "mention_count": count,
            # AND-merged in build_graph: stays True only when NO lecture-side
            # extraction also produced this concept — i.e. external-only.
            "from_external": True,
        })
        edges.append({
            "source": ext_id,
            "target": concept_id,
            "relation": "mentions",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": min(count / 5.0, 3.0),
            "source_file": _rel(path),
        })

    return {"nodes": nodes, "edges": edges}


def extract_from_reference(path: Path) -> dict:
    """Extract concepts from a references/*.md file."""
    text = path.read_text(encoding="utf-8")
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    label = first_line.lstrip("# ").strip() if first_line.startswith("#") else path.stem

    ref_id = f"ref_{path.stem}"
    nodes = [{"id": ref_id, "label": label, "type": "reference", "source_file": _rel(path)}]
    edges: list[dict] = []

    concepts = extract_concepts_from_text(text)
    concept_counts: Counter = Counter()
    for c in concepts:
        concept_counts[c["raw"]] += 1

    for concept_text, count in concept_counts.most_common(20):
        concept_id = f"concept_{slug(concept_text)}"
        nodes.append({
            "id": concept_id,
            "label": concept_text,
            "type": "concept",
            "source_file": _rel(path),
            "mention_count": count,
        })
        edges.append({
            "source": ref_id,
            "target": concept_id,
            "relation": "references",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "weight": 1.0,
            "source_file": _rel(path),
        })

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Graph building
# ---------------------------------------------------------------------------


def build_graph(extractions: list[dict]) -> "nx.Graph":
    """Merge all extraction dicts into a single NetworkX graph."""
    import networkx as nx

    G = nx.Graph()

    # Deduplicate nodes by id
    seen_nodes: dict[str, dict] = {}
    all_edges: list[dict] = []

    for extraction in extractions:
        for node in extraction.get("nodes", []):
            nid = node["id"]
            if nid not in seen_nodes:
                # copy: build_graph must not mutate the caller's extraction
                # dicts (the _links pop below would make a second call lossy)
                seen_nodes[nid] = dict(node)
            else:
                # Merge: keep richer version
                existing = seen_nodes[nid]
                if node.get("mention_count", 0) > existing.get("mention_count", 0):
                    existing["mention_count"] = node["mention_count"]
                if node.get("source_file") and not existing.get("source_file"):
                    existing["source_file"] = node["source_file"]
                # external-only marker: survives ONLY if every contribution
                # came from the external corpus (AND semantics).
                if existing.get("from_external") or node.get("from_external"):
                    existing["from_external"] = bool(
                        existing.get("from_external")) and bool(node.get("from_external"))
                # two docs collapsing onto one node keep the UNION of links
                if node.get("_links"):
                    merged = list(existing.get("_links") or [])
                    merged += [x for x in node["_links"] if x not in merged]
                    existing["_links"] = merged
                if node.get("_model_names"):
                    merged = list(existing.get("_model_names") or [])
                    have = {n for n, _ in merged}
                    merged += [p for p in node["_model_names"] if p[0] not in have]
                    existing["_model_names"] = merged
        all_edges.extend(extraction.get("edges", []))

    # External-card cross-links (frontmatter `links:`): pop the private key
    # BEFORE nodes enter the graph; keep an origin_id -> node id map so
    # targets resolve after every external node is known.
    ext_links: dict[str, list[str]] = {}
    ext_models: dict[str, list[list[str]]] = {}
    origin_map: dict[str, str] = {}
    for nid, attrs in seen_nodes.items():
        links = attrs.pop("_links", None)
        if links:
            ext_links[nid] = links
        models = attrs.pop("_model_names", None)
        if models:
            ext_models[nid] = models
        if attrs.get("type") == "external" and attrs.get("origin_id"):
            oid = attrs["origin_id"]
            if oid in origin_map and origin_map[oid] != nid:
                # duplicate origin ids would route links_to arbitrarily —
                # keep the first, but say so out loud.
                print(f"  WARNING: origin_id {oid} claimed by two external "
                      f"nodes ({origin_map[oid]} / {nid}) — links resolve "
                      f"to the first")
                continue
            origin_map[oid] = nid

    # Filter concept nodes by global frequency
    concept_freq: Counter = Counter()
    for edge in all_edges:
        for endpoint in [edge["source"], edge["target"]]:
            if endpoint.startswith("concept_"):
                concept_freq[endpoint] += 1

    # Add nodes
    for nid, attrs in seen_nodes.items():
        if nid.startswith("concept_") and concept_freq[nid] < MIN_CONCEPT_FREQUENCY:
            continue
        G.add_node(nid, **attrs)

    # Add edges (only between existing nodes)
    for edge in all_edges:
        src, tgt = edge["source"], edge["target"]
        if src in G and tgt in G:
            G.add_edge(
                src, tgt,
                relation=edge.get("relation", "related"),
                confidence=edge.get("confidence", "INFERRED"),
                confidence_score=edge.get("confidence_score", 0.5),
                weight=edge.get("weight", 1.0),
                source_file=edge.get("source_file"),
            )

    # EXTRACTED links_to edges: explicit card-to-card links carried by the
    # exporter — a link in the source card's live content is textual evidence,
    # the same level as a transcript mention.
    if ext_links:
        links_added = unresolved = 0
        for src_nid, links in ext_links.items():
            if src_nid not in G:
                continue
            for target in links:
                t_nid = origin_map.get(target)
                if t_nid is None:
                    unresolved += 1
                    continue
                if t_nid == src_nid or t_nid not in G:
                    continue
                if not G.has_edge(src_nid, t_nid):
                    G.add_edge(
                        src_nid, t_nid,
                        relation="links_to",
                        confidence="EXTRACTED",
                        confidence_score=1.0,
                        weight=1.5,
                        # provenance = the source card's doc (the link lives
                        # in that card's live content)
                        source_file=G.nodes[src_nid].get("source_file"),
                    )
                    links_added += 1
        print(f"  links_to edges: {links_added}"
              + (f" ({unresolved} unresolved targets)" if unresolved else ""))

    # Add INFERRED co-mention edges: concepts that appear in 2+ of the same
    # DOCUMENTS — a document is a video or an external card (both carry
    # EXTRACTED `mentions` edges, so co-occurrence means the same thing).
    concept_to_docs: dict[str, set[str]] = defaultdict(set)
    for src, tgt, data in G.edges(data=True):
        if data.get("relation") == "mentions":
            if (src.startswith("video_") or src.startswith("external_")) \
                    and tgt.startswith("concept_"):
                concept_to_docs[tgt].add(src)
            elif (tgt.startswith("video_") or tgt.startswith("external_")) \
                    and src.startswith("concept_"):
                concept_to_docs[src].add(tgt)

    # Find concept pairs that co-occur in the same documents
    concept_list = [c for c, vs in concept_to_docs.items() if len(vs) >= 2]
    for i, c1 in enumerate(concept_list):
        for c2 in concept_list[i + 1:]:
            shared = concept_to_docs[c1] & concept_to_docs[c2]
            if len(shared) >= 2 and not G.has_edge(c1, c2):
                score = min(len(shared) / 5.0, 1.0)
                G.add_edge(
                    c1, c2,
                    relation="co_mentioned",
                    confidence="INFERRED",
                    confidence_score=round(score, 2),
                    weight=round(score * 2, 2),
                    source_file=None,
                    shared_doc_count=len(shared),
                )

    # `describes` edges (placed AFTER the co-mention pass: relabeling a
    # mentions edge earlier would hide that doc-concept pair from
    # co-occurrence): an external doc's model name(s) -> the matching
    # concept node. Frontmatter names are exporter-curated (EXTRACTED);
    # self-mention/title fallbacks are heuristic (INFERRED). The doc-concept
    # `mentions` edge (if any) is UPGRADED in place — the graph is not a
    # multigraph — keeping the stronger confidence and weight.
    if ext_models:
        desc_counts: Counter = Counter()
        for src_nid, pairs in ext_models.items():
            if src_nid not in G:
                continue
            for name, sig in pairs:
                cid = f"concept_{slug(normalize_concept(name))}"
                if cid == src_nid or cid not in G:
                    continue
                conf = "EXTRACTED" if sig == "frontmatter" else "INFERRED"
                score = 1.0 if sig == "frontmatter" else 0.7
                if G.has_edge(src_nid, cid):
                    e = G.edges[src_nid, cid]
                    e["relation"] = "describes"
                    # confidence describes the NEW claim ("this doc is about
                    # that model"), not the old mention evidence — heuristic
                    # signals stay INFERRED even on an EXTRACTED mention.
                    e["confidence"] = conf
                    e["confidence_score"] = score
                    e["weight"] = max(e.get("weight", 0), 2.0)
                else:
                    G.add_edge(src_nid, cid, relation="describes",
                               confidence=conf, confidence_score=score,
                               weight=2.0,
                               source_file=G.nodes[src_nid].get("source_file"))
                desc_counts[sig] += 1
        if desc_counts:
            print(f"  describes edges: {sum(desc_counts.values())} "
                  f"(frontmatter {desc_counts.get('frontmatter', 0)}, "
                  f"self-mention {desc_counts.get('self-mention', 0)}, "
                  f"title {desc_counts.get('title', 0)})")

    # Alignment layer (graph_alignment.json):
    # 1) merged nodes carry their variant spellings, so queries match any form
    for canon, variants in _ALIGNMENT["alt_labels"].items():
        nid = f"concept_{slug(canon)}"
        if nid in G:
            G.nodes[nid]["alt_labels"] = list(variants)
    # 2) `aligned_with` edges between related-but-distinct concepts — added
    #    only when BOTH endpoints already exist (alignment never invents
    #    nodes), overriding a weaker co_mentioned edge if one is there.
    for group in _ALIGNMENT["align"]:
        ids = [f"concept_{slug(normalize_concept(x))}" for x in group]
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if a == b or a not in G or b not in G:
                    continue
                if G.has_edge(a, b):
                    # Only UPGRADE a weaker inferred co-mention; leave any
                    # other existing relation untouched (and drop the
                    # co_mentioned-specific attrs so none linger).
                    if G.edges[a, b].get("relation") != "co_mentioned":
                        continue
                    G.edges[a, b].pop("shared_doc_count", None)
                G.add_edge(
                    a, b,
                    relation="aligned_with",
                    confidence="ALIGNED",
                    confidence_score=1.0,
                    weight=2.0,
                    source_file=_rel(ALIGNMENT_PATH),
                )

    return G


# ---------------------------------------------------------------------------
# Community detection
# ---------------------------------------------------------------------------


def detect_communities(G: "nx.Graph") -> dict[str, int]:
    """Run Louvain community detection. Returns {node_id: community_id}."""
    import community as community_louvain

    if G.number_of_nodes() == 0:
        return {}

    partition = community_louvain.best_partition(G, resolution=1.0, random_state=42)
    return partition


def label_communities(G: "nx.Graph", partition: dict[str, int]) -> dict[int, str]:
    """Auto-label each community based on representative node labels."""
    communities: dict[int, list[str]] = defaultdict(list)
    for node_id, comm_id in partition.items():
        communities[comm_id].append(node_id)

    labels: dict[int, str] = {}
    for comm_id, members in communities.items():
        # Pick the most connected non-concept member, or most connected concept
        scored = []
        for nid in members:
            node_data = G.nodes[nid]
            degree = G.degree(nid)
            node_type = node_data.get("type", "")
            type_bonus = {"topic": 100, "series": 50, "reference": 30, "video": 5, "concept": 1}.get(node_type, 0)
            scored.append((type_bonus * 1000 + degree, node_data.get("label", nid)))
        scored.sort(reverse=True)
        labels[comm_id] = scored[0][1] if scored else f"Community {comm_id}"

    return labels


# ---------------------------------------------------------------------------
# Analysis (Graphify-style)
# ---------------------------------------------------------------------------


def god_nodes(G: "nx.Graph", top_n: int = 10) -> list[dict]:
    """Find the highest-degree nodes (what everything connects through)."""
    if G.number_of_nodes() == 0:
        return []

    by_degree = sorted(G.nodes(data=True), key=lambda x: G.degree(x[0]), reverse=True)
    result = []
    for nid, data in by_degree[:top_n]:
        result.append({
            "id": nid,
            "label": data.get("label", nid),
            "type": data.get("type", "unknown"),
            "degree": G.degree(nid),
            "neighbors": len(list(G.neighbors(nid))),
        })
    return result


def surprising_connections(G: "nx.Graph", partition: dict[str, int], top_n: int = 10) -> list[dict]:
    """Find edges that cross community boundaries — the non-obvious connections."""
    cross_edges = []
    for u, v, data in G.edges(data=True):
        cu = partition.get(u, -1)
        cv = partition.get(v, -1)
        if cu != cv and cu >= 0 and cv >= 0:
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            # Score: cross-type edges rank higher
            type_diversity = 1.0 if u_data.get("type") != v_data.get("type") else 0.5
            score = data.get("confidence_score", 0.5) * type_diversity * data.get("weight", 1.0)
            cross_edges.append({
                "source": u,
                "source_label": u_data.get("label", u),
                "source_type": u_data.get("type", ""),
                "target": v,
                "target_label": v_data.get("label", v),
                "target_type": v_data.get("type", ""),
                "relation": data.get("relation", ""),
                "confidence": data.get("confidence", ""),
                "score": round(score, 3),
            })

    cross_edges.sort(key=lambda x: -x["score"])
    return cross_edges[:top_n]


def suggest_questions(G: "nx.Graph", partition: dict[str, int], community_labels: dict[int, str]) -> list[str]:
    """Generate suggested questions the graph is positioned to answer."""
    gods = god_nodes(G, 5)
    surprises = surprising_connections(G, partition, 5)
    questions = []

    if gods:
        top = gods[0]
        questions.append(f"「{top['label']}」在李宏毅的課程中扮演什麼角色？為什麼這麼多概念都跟它有關？")
    if len(gods) >= 2:
        questions.append(f"「{gods[0]['label']}」和「{gods[1]['label']}」之間是什麼關係？")

    for surprise in surprises[:2]:
        questions.append(
            f"為什麼「{surprise['source_label']}」和「{surprise['target_label']}」會有關聯？"
        )

    if community_labels:
        comm_names = list(community_labels.values())[:3]
        if len(comm_names) >= 2:
            questions.append(
                f"「{comm_names[0]}」和「{comm_names[1]}」這兩個主題群之間有什麼交集？"
            )

    return questions[:5]


# ---------------------------------------------------------------------------
# Graph query
# ---------------------------------------------------------------------------


def query_graph(G: "nx.Graph", partition: dict[str, int], query: str, budget: int = 20) -> dict:
    """BFS-style query: find nodes matching the query, then explore neighbors."""
    import networkx as nx

    tokens = [t.casefold().strip() for t in re.split(r"[\s,;:()\"'`/]+", query) if t.strip()]
    tokens = [t for t in tokens if len(t) >= 2]

    # For Chinese tokens, also generate 2-char sub-tokens for partial matching
    # e.g. "語音模型" → ["語音", "模型"] so it can match nodes mentioning either
    zh_pattern = re.compile(r"[\u4e00-\u9fff]{2,}")
    extra_tokens = []
    for t in tokens:
        zh_parts = zh_pattern.findall(t)
        for part in zh_parts:
            if len(part) > 2:
                for i in range(len(part) - 1):
                    sub = part[i:i+2]
                    if sub not in tokens and sub not in extra_tokens:
                        extra_tokens.append(sub)
    all_tokens = tokens + extra_tokens

    # Also use the full query as a substring for Chinese compound terms
    full_query = query.casefold().strip()

    # Score all nodes by token match — against the label AND any merged
    # variant spellings (alt_labels), so e.g. "TTS" finds the 語音合成 node.
    scored = []
    for nid, data in G.nodes(data=True):
        label = data.get("label", "").casefold()
        alts = [a.casefold() for a in data.get("alt_labels", [])]
        haystacks = [label] + alts
        # Token-based scoring (original tokens score higher)
        score = sum(3 for t in tokens if any(t in h for h in haystacks))
        # Sub-token scoring (partial Chinese matches)
        score += sum(1 for t in extra_tokens if any(t in h for h in haystacks))
        # Full-query substring match
        if full_query and any(full_query in h for h in haystacks):
            score += 5
        # Also match node ID for concept nodes
        nid_lower = nid.lower()
        if any(t in nid_lower for t in all_tokens):
            score += 1
        if score > 0:
            scored.append((score, nid, data))

    scored.sort(key=lambda x: -x[0])
    seed_nodes = [nid for _, nid, _ in scored[:5]]

    if not seed_nodes:
        return {"query": query, "tokens": tokens, "results": [], "paths": []}

    # BFS from seed nodes
    visited = set()
    result_nodes = []
    queue = [(nid, 0) for nid in seed_nodes]

    while queue and len(result_nodes) < budget:
        current, depth = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        data = G.nodes[current]
        entry = {
            "id": current,
            "label": data.get("label", current),
            "type": data.get("type", ""),
            "community": partition.get(current, -1),
            "depth": depth,
            "degree": G.degree(current),
        }
        # Provenance for external-corpus nodes: consumers must frame these as
        # non-lecture sources (the user's notes/papers), never teacher content.
        if data.get("type") == "external":
            entry["source_type"] = data.get("source_type", "external")
            entry["collection"] = data.get("collection", "")
        # Concepts that ONLY external docs mention are provenance-marked too —
        # they must not read as lecture-graph vocabulary.
        if data.get("type") == "concept" and data.get("from_external"):
            entry["from_external"] = True
        if data.get("alt_labels"):
            entry["alt_labels"] = data["alt_labels"]
        result_nodes.append(entry)
        if depth < 2:
            for neighbor in G.neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

    # Find shortest paths between seed nodes
    paths = []
    for i, s1 in enumerate(seed_nodes):
        for s2 in seed_nodes[i + 1:]:
            try:
                path = nx.shortest_path(G, s1, s2)
                path_labels = [G.nodes[n].get("label", n) for n in path]
                paths.append({"from": s1, "to": s2, "path": path_labels, "length": len(path)})
            except nx.NetworkXNoPath:
                pass

    return {"query": query, "tokens": tokens, "results": result_nodes, "paths": paths}


# ---------------------------------------------------------------------------
# Report generation (Graphify-style GRAPH_REPORT.md)
# ---------------------------------------------------------------------------


def generate_report(
    G: "nx.Graph",
    partition: dict[str, int],
    community_labels: dict[int, str],
    corpus_stats: dict,
    output_suffix: str = "",
) -> str:
    """Generate a GRAPH_REPORT.md similar to Graphify's output."""
    gods = god_nodes(G, 10)
    surprises = surprising_connections(G, partition, 10)
    questions = suggest_questions(G, partition, community_labels)

    # Community stats
    community_sizes: Counter = Counter()
    for _, comm_id in partition.items():
        community_sizes[comm_id] += 1

    # Edge confidence / relation breakdown
    confidence_counts: Counter = Counter()
    relation_counts: Counter = Counter()
    for _, _, data in G.edges(data=True):
        confidence_counts[data.get("confidence", "UNKNOWN")] += 1
        relation_counts[data.get("relation", "?")] += 1

    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    lines = [
        "# Knowledge Graph Report",
        "",
        f"Generated: `{now}`",
        "",
        "## Corpus",
        "",
        f"- Files processed: `{corpus_stats.get('files_processed', 0)}`",
        f"- Transcripts with graph coverage: `{corpus_stats.get('transcripts', 0)}`",
        f"- Metadata-only videos: `{corpus_stats.get('metadata_only', 0)}`",
        f"- Topic pages: `{corpus_stats.get('topic_pages', 0)}`",
        f"- Reference docs: `{corpus_stats.get('reference_docs', 0)}`",
        *([f"- External docs: `{corpus_stats['external_docs']}`"]
          if corpus_stats.get("external_docs") else []),
        *[f"  - {coll}: `{n}`" for coll, n in sorted(
            (corpus_stats.get("external_collections") or {}).items())],
        "",
        "## Graph Stats",
        "",
        f"- Nodes: `{G.number_of_nodes()}`",
        f"- Edges: `{G.number_of_edges()}`",
        f"- Communities: `{len(community_sizes)}`",
        f"- EXTRACTED edges: `{confidence_counts.get('EXTRACTED', 0)}`",
        f"- INFERRED edges: `{confidence_counts.get('INFERRED', 0)}`",
        f"- AMBIGUOUS edges: `{confidence_counts.get('AMBIGUOUS', 0)}`",
        f"- ALIGNED edges: `{confidence_counts.get('ALIGNED', 0)}`"
        " (graph_alignment.json)",
        *([f"- links_to edges (external card cross-links): "
           f"`{relation_counts['links_to']}`"]
          if relation_counts.get("links_to") else []),
        *([f"- describes edges (external doc -> its model-name concept): "
           f"`{relation_counts['describes']}`"]
          if relation_counts.get("describes") else []),
        "",
        "## God Nodes",
        "",
        "Highest-degree concepts — what everything connects through.",
        "",
    ]

    for i, god in enumerate(gods, 1):
        lines.append(f"{i}. **{god['label']}** ({god['type']}) — degree {god['degree']}")

    lines.extend(["", "## Communities", ""])
    for comm_id, size in community_sizes.most_common():
        label = community_labels.get(comm_id, f"Community {comm_id}")
        lines.append(f"- **{label}** — {size} nodes")

    lines.extend(["", "## Surprising Connections", ""])
    lines.append("Edges that cross community boundaries — the non-obvious links.")
    lines.append("")

    for i, surprise in enumerate(surprises, 1):
        lines.append(
            f"{i}. **{surprise['source_label']}** ({surprise['source_type']}) "
            f"↔ **{surprise['target_label']}** ({surprise['target_type']}) "
            f"— {surprise['relation']} [{surprise['confidence']}]"
        )

    lines.extend(["", "## Suggested Questions", ""])
    lines.append("Questions the graph is uniquely positioned to answer:")
    lines.append("")
    for q in questions:
        lines.append(f"- {q}")

    lines.extend(["", "## How To Use This Graph", ""])
    lines.append("```bash")
    lines.append('python3 scripts/hungyi_kb.py graph query "attention mechanism"')
    lines.append('python3 scripts/hungyi_kb.py graph query "語音模型"')
    if not output_suffix:
        lines.append("python3 scripts/hungyi_kb.py graph report")
    lines.append("```")
    lines.append("")
    lines.append(f"Open `wiki/graph/graph{output_suffix}.html` in any browser for interactive exploration.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Export: graph.json
# ---------------------------------------------------------------------------


def export_json(G: "nx.Graph", partition: dict[str, int], path: Path) -> None:
    """Export graph as JSON (node-link format compatible with vis.js)."""
    from networkx.readwrite import json_graph
    data = json_graph.node_link_data(G, edges="links")

    # Annotate nodes with community
    for node in data["nodes"]:
        node["community"] = partition.get(node["id"], -1)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Export: graph.html (interactive vis.js visualization)
# ---------------------------------------------------------------------------

COMMUNITY_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#86bcb6", "#8cd17d", "#b6992d", "#499894", "#d37295",
    "#a0cbe8", "#ffbe7d", "#d4a6c8", "#fab0e4", "#7f7f7f",
]

TYPE_SHAPES = {
    "video": "dot",
    "concept": "diamond",
    "topic": "star",
    "series": "triangle",
    "reference": "square",
}


def export_html(
    G: "nx.Graph",
    partition: dict[str, int],
    community_labels: dict[int, str],
    path: Path,
) -> None:
    """Generate a standalone HTML file with vis.js for interactive exploration."""
    nodes_js = []
    for nid, data in G.nodes(data=True):
        comm = partition.get(nid, 0)
        color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]
        node_type = data.get("type", "concept")
        shape = TYPE_SHAPES.get(node_type, "dot")
        size = min(10 + G.degree(nid) * 2, 50)
        label_text = data.get("label", nid)
        if len(label_text) > 40:
            label_text = label_text[:37] + "..."
        title_text = html.escape(
            f"{data.get('label', nid)}\n"
            f"Type: {node_type}\n"
            f"Community: {community_labels.get(comm, comm)}\n"
            f"Degree: {G.degree(nid)}"
        )
        nodes_js.append({
            "id": nid,
            "label": label_text,
            "title": title_text,
            "color": color,
            "shape": shape,
            "size": size,
            "group": comm,
        })

    edges_js = []
    for u, v, data in G.edges(data=True):
        edge_color = {"EXTRACTED": "#888", "INFERRED": "#bbb", "AMBIGUOUS": "#f44"}.get(
            data.get("confidence", ""), "#ccc"
        )
        edges_js.append({
            "from": u,
            "to": v,
            "title": html.escape(f"{data.get('relation', '')} [{data.get('confidence', '')}]"),
            "color": {"color": edge_color, "opacity": 0.6},
            "width": max(1, min(data.get("weight", 1.0), 4)),
        })

    community_legend = json.dumps(
        {str(k): v for k, v in community_labels.items()}, ensure_ascii=False
    )

    html_content = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<title>Hung-Yi Lee Knowledge Graph</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #1a1a2e; color: #e0e0e0; }}
  #controls {{ position: fixed; top: 0; left: 0; right: 0; z-index: 10;
               background: rgba(26, 26, 46, 0.95); padding: 12px 20px;
               display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #333; }}
  #controls h1 {{ font-size: 16px; white-space: nowrap; }}
  #search {{ flex: 1; max-width: 400px; padding: 6px 12px; border-radius: 6px;
             border: 1px solid #444; background: #16213e; color: #e0e0e0; font-size: 14px; }}
  #stats {{ font-size: 12px; color: #888; white-space: nowrap; }}
  #graph {{ width: 100vw; height: 100vh; padding-top: 50px; }}
  #legend {{ position: fixed; bottom: 16px; right: 16px; background: rgba(26, 26, 46, 0.9);
             padding: 12px; border-radius: 8px; font-size: 11px; max-height: 300px;
             overflow-y: auto; border: 1px solid #333; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; margin: 3px 0; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
</style>
</head>
<body>
<div id="controls">
  <h1>🎓 Hung-Yi Lee Knowledge Graph</h1>
  <input id="search" type="text" placeholder="Search nodes..." />
  <span id="stats">{G.number_of_nodes()} nodes · {G.number_of_edges()} edges · {len(community_labels)} communities</span>
</div>
<div id="graph"></div>
<div id="legend"></div>
<script>
var nodesData = {json.dumps(nodes_js, ensure_ascii=False)};
var edgesData = {json.dumps(edges_js, ensure_ascii=False)};
var communityLabels = {community_legend};

var nodes = new vis.DataSet(nodesData);
var edges = new vis.DataSet(edgesData);
var container = document.getElementById("graph");
var data = {{ nodes: nodes, edges: edges }};
var options = {{
  physics: {{ solver: "forceAtlas2Based", forceAtlas2Based: {{ gravitationalConstant: -80, springLength: 120 }},
              stabilization: {{ iterations: 150 }} }},
  interaction: {{ hover: true, tooltipDelay: 100, navigationButtons: true }},
  nodes: {{ font: {{ color: "#e0e0e0", size: 11 }} }},
  edges: {{ smooth: {{ type: "continuous" }} }},
}};
var network = new vis.Network(container, data, options);

// Search
document.getElementById("search").addEventListener("input", function(e) {{
  var q = e.target.value.toLowerCase();
  if (!q) {{ nodes.forEach(function(n) {{ nodes.update({{id: n.id, hidden: false}}); }}); return; }}
  nodes.forEach(function(n) {{
    var match = n.label.toLowerCase().indexOf(q) >= 0 || (n.title && n.title.toLowerCase().indexOf(q) >= 0);
    nodes.update({{id: n.id, hidden: !match}});
  }});
}});

// Legend
var legend = document.getElementById("legend");
var usedComms = new Set(nodesData.map(function(n) {{ return n.group; }}));
var colors = {json.dumps(COMMUNITY_COLORS)};
var html = "<b>Communities</b><br>";
usedComms.forEach(function(c) {{
  var label = communityLabels[String(c)] || "Community " + c;
  var color = colors[c % colors.length];
  html += '<div class="legend-item"><span class="legend-dot" style="background:' + color + '"></span>' + label + "</div>";
}});
legend.innerHTML = html;
</script>
</body>
</html>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------


def build_full_graph(
    transcripts_dir: Path,
    topics_dir: Path,
    references_dir: Path,
    channel_index_path: Path,
    output_dir: Path,
    external_dir: Path | None = None,
    output_suffix: str = "",
) -> dict:
    """Run the full graph pipeline: detect → extract → build → cluster → analyze → export.

    `external_dir` (raw/external/) mixes in gitignored external corpora; pair
    it with `output_suffix=".local"` so the mixed graph lands in
    graph.local.json / GRAPH_REPORT.local.md / graph.local.html and the
    tracked lecture-only outputs stay untouched."""
    output_dir.mkdir(parents=True, exist_ok=True)

    extractions: list[dict] = []
    stats = {
        "files_processed": 0,
        "transcripts": 0,
        "metadata_only": 0,
        "topic_pages": 0,
        "reference_docs": 0,
        "external_docs": 0,
    }

    # 1. Extract from transcripts
    transcript_ids = set()
    for path in sorted(transcripts_dir.glob("*.md")):
        extraction = extract_from_transcript(path)
        extractions.append(extraction)
        stats["transcripts"] += 1
        stats["files_processed"] += 1
        # Track which video IDs have transcripts
        for node in extraction["nodes"]:
            if node.get("type") == "video" and node.get("video_id"):
                transcript_ids.add(node["video_id"])
    print(f"  Transcripts: {stats['transcripts']} files extracted")

    # 2. Extract metadata-only videos
    if channel_index_path.exists():
        channel_data = json.loads(channel_index_path.read_text(encoding="utf-8"))
        for video in channel_data.get("videos", []):
            if video["video_id"] not in transcript_ids:
                extraction = extract_from_metadata(video)
                extractions.append(extraction)
                stats["metadata_only"] += 1
                stats["files_processed"] += 1
    print(f"  Metadata-only: {stats['metadata_only']} videos")

    # 3. Extract from wiki topic pages
    for path in sorted(topics_dir.glob("*.md")):
        extraction = extract_from_wiki_topic(path)
        extractions.append(extraction)
        stats["topic_pages"] += 1
        stats["files_processed"] += 1
    print(f"  Topic pages: {stats['topic_pages']}")

    # 4. Extract from reference docs
    for path in sorted(references_dir.glob("*.md")):
        extraction = extract_from_reference(path)
        extractions.append(extraction)
        stats["reference_docs"] += 1
        stats["files_processed"] += 1
    print(f"  References: {stats['reference_docs']}")

    # 4b. Extract from external corpora (raw/external/<collection>/*.md)
    if external_dir is not None and external_dir.exists():
        ext_collections: Counter = Counter()
        for path in sorted(external_dir.glob("*/*.md")):
            extraction = extract_from_external(path)
            extractions.append(extraction)
            stats["external_docs"] += 1
            stats["files_processed"] += 1
            # count by the doc's LOGICAL collection (frontmatter) — that is
            # what node provenance carries — not the directory name
            ext_collections[extraction["nodes"][0].get("collection")
                            or path.parent.name] += 1
        if ext_collections:
            stats["external_collections"] = dict(ext_collections)
        print(f"  External docs: {stats['external_docs']} "
              + " ".join(f"{k}={v}" for k, v in sorted(ext_collections.items())))

    # 5. Build graph
    print("Building graph...")
    G = build_graph(extractions)
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # 6. Community detection
    print("Detecting communities...")
    partition = detect_communities(G)
    community_labels = label_communities(G, partition)
    num_communities = len(set(partition.values())) if partition else 0
    print(f"  Communities: {num_communities}")

    # 7. Generate report
    print("Generating report...")
    report = generate_report(G, partition, community_labels, stats,
                             output_suffix=output_suffix)
    report_path = output_dir / f"GRAPH_REPORT{output_suffix}.md"
    report_path.write_text(report, encoding="utf-8")

    # 8. Export JSON
    json_path = output_dir / f"graph{output_suffix}.json"
    export_json(G, partition, json_path)

    # 9. Export HTML
    html_path = output_dir / f"graph{output_suffix}.html"
    export_html(G, partition, community_labels, html_path)

    print(f"\nGraph complete. Outputs in {output_dir}/")
    print(f"  GRAPH_REPORT{output_suffix}.md  — god nodes, surprising connections, suggested questions")
    print(f"  graph{output_suffix}.json       — persistent queryable graph ({G.number_of_nodes()} nodes)")
    print(f"  graph{output_suffix}.html       — interactive visualization (open in browser)")

    return {
        "stats": stats,
        "graph_nodes": G.number_of_nodes(),
        "graph_edges": G.number_of_edges(),
        "communities": num_communities,
        "output_dir": str(output_dir),
    }
