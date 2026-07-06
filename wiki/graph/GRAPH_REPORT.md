# Knowledge Graph Report

Generated: `2026-07-06T08:36:40+00:00`

## Corpus

- Files processed: `491`
- Transcripts with graph coverage: `27`
- Metadata-only videos: `451`
- Topic pages: `8`
- Reference docs: `5`

## Graph Stats

- Nodes: `927`
- Edges: `4137`
- Communities: `9`
- EXTRACTED edges: `1696`
- INFERRED edges: `2439`
- AMBIGUOUS edges: `0`
- ALIGNED edges: `2` (graph_alignment.json)

## God Nodes

Highest-degree concepts — what everything connects through.

1. **Ml Fundamentals** (topic) — degree 387
2. **機器學習** (concept) — degree 231
3. **語言模型** (concept) — degree 175
4. **Standalone Talks** (series) — degree 148
5. **Llama** (concept) — degree 109
6. **Claude** (concept) — degree 97
7. **Diffusion And Generation** (topic) — degree 96
8. **Gemini** (concept) — degree 95
9. **Transformer** (concept) — degree 91
10. **語音辨識** (concept) — degree 87

## Communities

- **Ml Fundamentals** — 441 nodes
- **Diffusion And Generation** — 120 nodes
- **AI Agent (3/3)** — 86 nodes
- **Speech And Audio** — 79 nodes
- **機器學習2021** — 71 nodes
- **[ML 2021 (English version)] Lecture 17** — 57 nodes
- **Evaluation And Benchmarks** — 44 nodes
- **Model Editing And Merging** — 23 nodes
- **[ICASSP 2020] TRAINING CODE-SWITCHING LANGUAGE MODEL WITH MONOLINGUAL DATA (Speaker** — 6 nodes

## Surprising Connections

Edges that cross community boundaries — the non-obvious links.

1. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型** (video) — mentions [EXTRACTED]
2. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】第五講：大型語言模型訓練方法「預訓練–對齊」(Pretrain-Alignment) 的強大與極限** (video) — mentions [EXTRACTED]
3. **語言模型** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第１講：一堂課搞懂生成式人工智慧的原理** (video) — mentions [EXTRACTED]
4. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】第七講：DeepSeek-R1 這類大型語言模型是如何進行「深度思考」（Reasoning）的？** (video) — mentions [EXTRACTED]
5. **語言模型** (concept) ↔ **【生成式AI時代下的機器學習(2025)】助教課：利用多張GPU訓練大型語言模型—從零開始介紹DeepSpeed、Liger Kernel、Flash Attention及Quantization** (video) — mentions [EXTRACTED]
6. **語言模型** (concept) ↔ **加快語言模型生成速度 (1/2)：Flash Attention** (video) — mentions [EXTRACTED]
7. **語音辨識** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 8 講：通用模型的終身學習 (Fine-tuning, Model Editing, Model Merging, Test-Time Training)** (video) — mentions [EXTRACTED]
8. **【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型** (video) ↔ **Llama** (concept) — mentions [EXTRACTED]
9. **【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型** (video) ↔ **Gemma** (concept) — mentions [EXTRACTED]
10. **Deep Learning** (concept) ↔ **【生成式人工智慧與機器學習導論2025】第 10 講：語音語言模型發展史 (本課程前段內容為歷史回顧，2025 年的技術從 1:42:00 開始)** (video) — mentions [EXTRACTED]

## Suggested Questions

Questions the graph is uniquely positioned to answer:

- 「Ml Fundamentals」在李宏毅的課程中扮演什麼角色？為什麼這麼多概念都跟它有關？
- 「Ml Fundamentals」和「機器學習」之間是什麼關係？
- 為什麼「語言模型」和「【生成式人工智慧與機器學習導論2025】第3講：解剖大型語言模型」會有關聯？
- 為什麼「語言模型」和「【生成式AI時代下的機器學習(2025)】第五講：大型語言模型訓練方法「預訓練–對齊」(Pretrain-Alignment) 的強大與極限」會有關聯？
- 「AI Agent (3/3)」和「Diffusion And Generation」這兩個主題群之間有什麼交集？

## How To Use This Graph

```bash
python3 scripts/hungyi_kb.py graph query "attention mechanism"
python3 scripts/hungyi_kb.py graph query "語音模型"
python3 scripts/hungyi_kb.py graph report
```

Open `wiki/graph/graph.html` in any browser for interactive exploration.
