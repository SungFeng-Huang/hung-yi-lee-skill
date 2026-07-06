# Knowledge Graph Report

Generated: `2026-07-06T07:39:08+00:00`

## Corpus

- Files processed: `491`
- Transcripts with graph coverage: `27`
- Metadata-only videos: `451`
- Topic pages: `8`
- Reference docs: `5`

## Graph Stats

- Nodes: `929`
- Edges: `4124`
- Communities: `9`
- EXTRACTED edges: `1695`
- INFERRED edges: `2429`
- AMBIGUOUS edges: `0`

## God Nodes

Highest-degree concepts — what everything connects through.

1. **Ml Fundamentals** (topic) — degree 387
2. **機器學習** (concept) — degree 230
3. **語言模型** (concept) — degree 174
4. **Standalone Talks** (series) — degree 148
5. **Llama** (concept) — degree 109
6. **Claude** (concept) — degree 97
7. **Diffusion And Generation** (topic) — degree 96
8. **Gemini** (concept) — degree 95
9. **Transformer** (concept) — degree 90
10. **評估** (concept) — degree 85

## Communities

- **Ml Fundamentals** — 438 nodes
- **Diffusion And Generation** — 101 nodes
- **Speech And Audio** — 80 nodes
- **Model Editing And Merging** — 79 nodes
- **機器學習2021** — 66 nodes
- **Agents And Context** — 63 nodes
- **[ML 2021 (English version)] Lecture 17** — 48 nodes
- **Evaluation And Benchmarks** — 48 nodes
- **[ICASSP 2020] TRAINING CODE-SWITCHING LANGUAGE MODEL WITH MONOLINGUAL DATA (Speaker** — 6 nodes

## Surprising Connections

Edges that cross community boundaries — the non-obvious links.

1. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **Claude** (concept) — mentions [EXTRACTED]
2. **Gemini** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 4 講：評估生成式人工智慧能力時可能遇到的各種坑** (video) — mentions [EXTRACTED]
3. **Claude** (concept) ↔ **AI Agent (3/3): AI Agent 對於工作帶來的衝擊 - 以學術研究為例** (video) — mentions [EXTRACTED]
4. **Claude** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 4 講：評估生成式人工智慧能力時可能遇到的各種坑** (video) — mentions [EXTRACTED]
5. **Claude** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 2 講：上下文工程 (Context Engineering) — AI Agent 背後的關鍵技術** (video) — mentions [EXTRACTED]
6. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型** (video) — mentions [EXTRACTED]
7. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 10 講：語音語言模型發展史 (本課程前段內容為歷史回顧，2025 年的技術從 1:42:00 開始)** (video) — mentions [EXTRACTED]
8. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 7 講：大型語言模型的學習歷程** (video) — mentions [EXTRACTED]
9. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】第十二講：語言模型如何學會說話 — 概述語音語言模型發展歷程** (video) — mentions [EXTRACTED]
10. **語言模型** (concept) ↔ **加快語言模型生成速度 (1/2)：Flash Attention** (video) — mentions [EXTRACTED]

## Suggested Questions

Questions the graph is uniquely positioned to answer:

- 「Ml Fundamentals」在李宏毅的課程中扮演什麼角色？為什麼這麼多概念都跟它有關？
- 「Ml Fundamentals」和「機器學習」之間是什麼關係？
- 為什麼「解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理」和「Claude」會有關聯？
- 為什麼「Gemini」和「【生成式人工智慧與機器學習導論2025】第 4 講：評估生成式人工智慧能力時可能遇到的各種坑」會有關聯？
- 「Agents And Context」和「Model Editing And Merging」這兩個主題群之間有什麼交集？

## How To Use This Graph

```bash
python3 scripts/hungyi_kb.py graph query "attention mechanism"
python3 scripts/hungyi_kb.py graph query "語音模型"
python3 scripts/hungyi_kb.py graph report
```

Open `wiki/graph/graph.html` in any browser for interactive exploration.
