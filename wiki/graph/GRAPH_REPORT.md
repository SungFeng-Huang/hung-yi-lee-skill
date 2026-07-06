# Knowledge Graph Report

Generated: `2026-07-06T07:20:24+00:00`

## Corpus

- Files processed: `491`
- Transcripts with graph coverage: `27`
- Metadata-only videos: `451`
- Topic pages: `8`
- Reference docs: `5`

## Graph Stats

- Nodes: `929`
- Edges: `4098`
- Communities: `9`
- EXTRACTED edges: `1693`
- INFERRED edges: `2405`
- AMBIGUOUS edges: `0`

## God Nodes

Highest-degree concepts — what everything connects through.

1. **Ml Fundamentals** (topic) — degree 387
2. **機器學習** (concept) — degree 229
3. **語言模型** (concept) — degree 175
4. **Standalone Talks** (series) — degree 148
5. **Llama** (concept) — degree 109
6. **Claude** (concept) — degree 96
7. **Diffusion And Generation** (topic) — degree 96
8. **Gemini** (concept) — degree 94
9. **Transformer** (concept) — degree 89
10. **評估** (concept) — degree 84

## Communities

- **Ml Fundamentals** — 406 nodes
- **Diffusion And Generation** — 153 nodes
- **Speech And Audio** — 81 nodes
- **Review** — 80 nodes
- **Evaluation And Benchmarks** — 77 nodes
- **AI Agent (3/3)** — 73 nodes
- **Model Editing And Merging** — 28 nodes
- **生成式人工智慧與機器學習導論2025** — 25 nodes
- **[ICASSP 2020] TRAINING CODE-SWITCHING LANGUAGE MODEL WITH MONOLINGUAL DATA (Speaker** — 6 nodes

## Surprising Connections

Edges that cross community boundaries — the non-obvious links.

1. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **Claude** (concept) — mentions [EXTRACTED]
2. **Claude** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 2 講：上下文工程 (Context Engineering) — AI Agent 背後的關鍵技術** (video) — mentions [EXTRACTED]
3. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 10 講：語音語言模型發展史 (本課程前段內容為歷史回顧，2025 年的技術從 1:42:00 開始)** (video) — mentions [EXTRACTED]
4. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 7 講：大型語言模型的學習歷程** (video) — mentions [EXTRACTED]
5. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 4 講：評估生成式人工智慧能力時可能遇到的各種坑** (video) — mentions [EXTRACTED]
6. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】第十二講：語言模型如何學會說話 — 概述語音語言模型發展歷程** (video) — mentions [EXTRACTED]
7. **語音辨識** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 8 講：通用模型的終身學習 (Fine-tuning, Model Editing, Model Merging, Test-Time Training)** (video) — mentions [EXTRACTED]
8. **【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型** (video) ↔ **Llama** (concept) — mentions [EXTRACTED]
9. **【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型** (video) ↔ **Gemma** (concept) — mentions [EXTRACTED]
10. **Deep Learning** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 10 講：語音語言模型發展史 (本課程前段內容為歷史回顧，2025 年的技術從 1:42:00 開始)** (video) — mentions [EXTRACTED]

## Suggested Questions

Questions the graph is uniquely positioned to answer:

- 「Ml Fundamentals」在李宏毅的課程中扮演什麼角色？為什麼這麼多概念都跟它有關？
- 「Ml Fundamentals」和「機器學習」之間是什麼關係？
- 為什麼「解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理」和「Claude」會有關聯？
- 為什麼「Claude」和「【生成式人工智慧與機器學習導論2025】第 2 講：上下文工程 (Context Engineering) — AI Agent 背後的關鍵技術」會有關聯？
- 「Diffusion And Generation」和「AI Agent (3/3)」這兩個主題群之間有什麼交集？

## How To Use This Graph

```bash
python3 scripts/hungyi_kb.py graph query "attention mechanism"
python3 scripts/hungyi_kb.py graph query "語音模型"
python3 scripts/hungyi_kb.py graph report
```

Open `wiki/graph/graph.html` in any browser for interactive exploration.
