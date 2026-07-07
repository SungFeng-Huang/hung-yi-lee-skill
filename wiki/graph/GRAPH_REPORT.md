# Knowledge Graph Report

Generated: `2026-07-07T15:09:07+00:00`

## Corpus

- Files processed: `495`
- Transcripts with graph coverage: `44`
- Metadata-only videos: `438`
- Topic pages: `8`
- Reference docs: `5`

## Graph Stats

- Nodes: `967`
- Edges: `4910`
- Communities: `8`
- EXTRACTED edges: `1978`
- INFERRED edges: `2930`
- AMBIGUOUS edges: `0`
- ALIGNED edges: `2` (graph_alignment.json)

## God Nodes

Highest-degree concepts — what everything connects through.

1. **Ml Fundamentals** (topic) — degree 390
2. **機器學習** (concept) — degree 263
3. **語言模型** (concept) — degree 214
4. **Standalone Talks** (series) — degree 151
5. **Language Model** (concept) — degree 136
6. **ChatGPT** (concept) — degree 125
7. **Llama** (concept) — degree 119
8. **Claude** (concept) — degree 118
9. **OpenAI** (concept) — degree 118
10. **Gemini** (concept) — degree 114

## Communities

- **Ml Fundamentals** — 528 nodes
- **Diffusion And Generation** — 136 nodes
- **Harness Engineering** — 94 nodes
- **Speech And Audio** — 94 nodes
- **[ML 2021 (English version)] Lecture 17** — 45 nodes
- **生成式人工智慧與機器學習導論2025** — 32 nodes
- **Model Editing And Merging** — 27 nodes
- **Agents And Context** — 11 nodes

## Surprising Connections

Edges that cross community boundaries — the non-obvious links.

1. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **語言模型** (concept) — mentions [EXTRACTED]
2. **解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理** (video) ↔ **語音合成** (concept) — mentions [EXTRACTED]
3. **AI Agent** (concept) ↔ **Is AI Crossing the Rubicon? How Far Are We from Self-Improving AI? (Part 2)** (video) — mentions [EXTRACTED]
4. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 10 講：語音語言模型發展史 (本課程前段內容為歷史回顧，2025 年的技術從 1:42:00 開始)** (video) — mentions [EXTRACTED]
5. **語言模型** (concept) ↔ **GPT-4o 背後可能的語音技術猜測** (video) — mentions [EXTRACTED]
6. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】第一講：一堂課搞懂生成式人工智慧的技術突破與未來發展** (video) — mentions [EXTRACTED]
7. **語言模型** (concept) ↔ **Harness Engineering: Sometimes Language Models Aren't Unintelligent, They Just Lack Proper Human ...** (video) — mentions [EXTRACTED]
8. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 7 講：大型語言模型的學習歷程** (video) — mentions [EXTRACTED]
9. **語言模型** (concept) ↔ **Is AI Crossing the Rubicon? How Far Are We from Self-Improving AI? (Part 2)** (video) — mentions [EXTRACTED]
10. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 4 講：評估生成式人工智慧能力時可能遇到的各種坑** (video) — mentions [EXTRACTED]

## Suggested Questions

Questions the graph is uniquely positioned to answer:

- 「Ml Fundamentals」在李宏毅的課程中扮演什麼角色？為什麼這麼多概念都跟它有關？
- 「Ml Fundamentals」和「機器學習」之間是什麼關係？
- 為什麼「解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理」和「語言模型」會有關聯？
- 為什麼「解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理」和「語音合成」會有關聯？
- 「Harness Engineering」和「生成式人工智慧與機器學習導論2025」這兩個主題群之間有什麼交集？

## How To Use This Graph

```bash
python3 scripts/hungyi_kb.py graph query "attention mechanism"
python3 scripts/hungyi_kb.py graph query "語音模型"
python3 scripts/hungyi_kb.py graph report
```

Open `wiki/graph/graph.html` in any browser for interactive exploration.
