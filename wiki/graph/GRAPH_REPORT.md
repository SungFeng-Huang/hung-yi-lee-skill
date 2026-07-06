# Knowledge Graph Report

Generated: `2026-07-06T15:09:43+00:00`

## Corpus

- Files processed: `495`
- Transcripts with graph coverage: `44`
- Metadata-only videos: `438`
- Topic pages: `8`
- Reference docs: `5`

## Graph Stats

- Nodes: `948`
- Edges: `4751`
- Communities: `6`
- EXTRACTED edges: `1933`
- INFERRED edges: `2816`
- AMBIGUOUS edges: `0`
- ALIGNED edges: `2` (graph_alignment.json)

## God Nodes

Highest-degree concepts — what everything connects through.

1. **Ml Fundamentals** (topic) — degree 389
2. **機器學習** (concept) — degree 256
3. **語言模型** (concept) — degree 206
4. **Standalone Talks** (series) — degree 151
5. **Claude** (concept) — degree 128
6. **Llama** (concept) — degree 120
7. **Transformer** (concept) — degree 114
8. **Gemini** (concept) — degree 110
9. **Language Model** (concept) — degree 102
10. **語音辨識** (concept) — degree 101

## Communities

- **Ml Fundamentals** — 468 nodes
- **Speech And Audio** — 152 nodes
- **Diffusion And Generation** — 126 nodes
- **李宏毅老師訪談腳本 — 一問一答版** — 87 nodes
- **Model Editing And Merging** — 77 nodes
- **Agents And Context** — 38 nodes

## Surprising Connections

Edges that cross community boundaries — the non-obvious links.

1. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **Claude** (concept) — mentions [EXTRACTED]
2. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **語言模型** (concept) — mentions [EXTRACTED]
3. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **語音合成** (concept) — mentions [EXTRACTED]
4. **AI Agent** (concept) ↔ **Is AI Crossing the Rubicon? How Far Are We from Self-Improving AI? (Part 2)** (video) — mentions [EXTRACTED]
5. **Claude** (concept) ↔ **AI Agent (3/3): AI Agent 對於工作帶來的衝擊 - 以學術研究為例** (video) — mentions [EXTRACTED]
6. **Claude** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 2 講：上下文工程 (Context Engineering) — AI Agent 背後的關鍵技術** (video) — mentions [EXTRACTED]
7. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 10 講：語音語言模型發展史 (本課程前段內容為歷史回顧，2025 年的技術從 1:42:00 開始)** (video) — mentions [EXTRACTED]
8. **語言模型** (concept) ↔ **GPT-4o 背後可能的語音技術猜測** (video) — mentions [EXTRACTED]
9. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】第一講：一堂課搞懂生成式人工智慧的技術突破與未來發展** (video) — mentions [EXTRACTED]
10. **語言模型** (concept) ↔ **Harness Engineering: Sometimes Language Models Aren't Unintelligent, They Just Lack Proper Human ...** (video) — mentions [EXTRACTED]

## Suggested Questions

Questions the graph is uniquely positioned to answer:

- 「Ml Fundamentals」在李宏毅的課程中扮演什麼角色？為什麼這麼多概念都跟它有關？
- 「Ml Fundamentals」和「機器學習」之間是什麼關係？
- 為什麼「解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理」和「Claude」會有關聯？
- 為什麼「解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理」和「語言模型」會有關聯？
- 「Agents And Context」和「李宏毅老師訪談腳本 — 一問一答版」這兩個主題群之間有什麼交集？

## How To Use This Graph

```bash
python3 scripts/hungyi_kb.py graph query "attention mechanism"
python3 scripts/hungyi_kb.py graph query "語音模型"
python3 scripts/hungyi_kb.py graph report
```

Open `wiki/graph/graph.html` in any browser for interactive exploration.
