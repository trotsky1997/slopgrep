# Dissertation chapters slopgrep report

Scan target: `/mnt/c/Users/trots/Documents/phd_dissertation/docs/chapters`

Command used:

```bash
python3 -m slopgrep scan /mnt/c/Users/trots/Documents/phd_dissertation/docs/chapters \
  --include '*.md' --include '*.txt' --include '*.tex' --json
```

## Executive view

- Scanned files with findings: 10
- Files with likely substantive findings after filtering obvious formatting noise: 9
- Most findings come from `ai.zh.vocab`, which is a broad heuristic and should be treated as a style prompt, not proof of AI-generated text.
- The largest source of false positives is LaTeX-friendly Chinese typography: `“”`, `—`, and technical table phrasing.
- The most review-worthy chapters are `introduction.tex`, `related_work.tex`, `conclusion.tex`, and `chapter3_agentic_reasoning.tex`.

## False-positive patterns to downweight

These rule families triggered often but are weak evidence in this dissertation context:

- `ai.unicode.decoration`: Chinese quotes and typography are normal in LaTeX prose.
- `ai.emdash.addiction`: many hits are term connectors such as `图像—文本—领域知识` rather than dramatic AI punctuation.
- `ai.zh.vocab`: useful for surfacing abstract wording density, but high-frequency academic phrases will trigger it.

## Prioritized files

### 1. `introduction.tex`

Filtered score: 18

Why it stands out:
- Dense abstract wording around "能力增强", "重要方向", "工具增强任务", "证据一致性", "真实任务执行"
- Several table and roadmap lines repeat the same high-level framing
- Reads more like polished survey prose than direct dissertation argument in a few places

Representative lines:
- `introduction.tex:6` long opening paragraph with multiple abstract capability phrases
- `introduction.tex:18` process-supervision paragraph uses compressed conceptual vocabulary
- `introduction.tex:34` and `introduction.tex:35` table rows repeat `增强` and `执行` framing
- `introduction.tex:56` roadmap sentence compresses the thesis into a neat three-stage arc

Review advice:
- Prefer concrete task or method names where possible
- Trim repeated uses of `增强`, `能力`, `过程`, `任务执行`
- Check whether the opening paragraph can carry more evidence and fewer umbrella labels

### 2. `chapter3_agentic_reasoning.tex`

Filtered score: 10

Why it stands out:
- Contains a real `ai.zh.analysis` hit, not just vocabulary density
- Some summary sentences collapse multiple contributions into a polished conceptual arc

Representative lines:
- `chapter3_agentic_reasoning.tex:329` `展示了模型如何通过工具规划与执行，把内部推理推进到化学与材料科学任务中。`
- `chapter3_agentic_reasoning.tex:168` uses a tidy conceptual reframe from single-generation to explicit search and ranking

Review advice:
- Watch for `表明/展示了/说明` endings that over-summarize
- Replace concept-heavy restatements with more concrete claims about what each method changes

### 3. `related_work.tex`

Filtered score: 9

Why it stands out:
- One substantive `ai.zh.analysis` hit
- Several sentences use large-scope framing such as `统一研究方向`, `更稳定、更可扩展`, `获得更高上限`

Representative lines:
- `related_work.tex:78` `展示了测试时搜索在程序生成、网页导航和问答任务中的广泛适用性`
- `related_work.tex:66` `建立一套更稳定、更可扩展的复杂推理增强体系`
- `related_work.tex:72` `获得更高上限`

Review advice:
- In related work, broad synthesis is normal, but these lines can be tightened by naming the evidence instead of the takeaway
- `广泛适用性`, `统一研究方向`, `更高上限` are good candidates for plainer wording

### 4. `conclusion.tex`

Filtered score: 8

Why it stands out:
- Summary voice is naturally more vulnerable to template-like phrasing
- One structural hit on future-outlook heading

Representative lines:
- `conclusion.tex:6` opening summary compresses the whole thesis into a neat three-step answer
- `conclusion.tex:12` `重点已经不再是...而是...` style framing feels more rhetorical than necessary
- `conclusion.tex:101` `\section{研究工作的未来展望}` flagged as a standard future-outlook template

Review advice:
- Conclusions can stay structured, but avoid overly smooth totalizing lines
- Consider whether some summary claims can point back to chapter evidence more explicitly

### 5. `chapter1_domain_lm.tex`

Filtered score: 7

Why it stands out:
- Mostly not AI-sounding, but some lines over-explain the thesis significance
- A few paragraphs generalize from experimental results to broad capability claims

Representative lines:
- `chapter1_domain_lm.tex:52` methodological summary framed as a thesis-wide principle
- `chapter1_domain_lm.tex:264` and `chapter1_domain_lm.tex:295` use phrases like `系统增强`, `整体增强`, `一般化表现`

Review advice:
- Distinguish clearly between measured gains and broader interpretation
- Swap broad capability labels for the specific benchmark or behavior observed

## Lower-priority files

These were flagged mainly by broad vocabulary heuristics and look less urgent:

- `appendix_experiments.tex`
- `appendix_cases.tex`
- `publications.tex`
- `abbreviations.tex`

## Overall judgment

The chapters do not look like raw chatbot prose. The scan did not surface classic assistant residue such as `希望这对您有帮助`, `当然`, or training-cutoff disclaimers.

What it did surface is narrower:
- abstract academic wording is sometimes too dense
- some transition and summary sentences feel a bit too polished or totalizing
- a few lines in survey and conclusion sections use `说明/展示/走向/增强` in a repetitive way

In short: this reads more like highly smoothed academic prose than obvious AI slop.

## Suggested next pass

If you want a manual review pass, start here:

1. `introduction.tex`
2. `related_work.tex`
3. `conclusion.tex`
4. `chapter3_agentic_reasoning.tex`

For those files, focus on:
- repeated abstract nouns
- sentences that end by declaring significance
- tidy three-stage or `不是...而是...` summary structures
- broad claims that could be replaced by evidence or chapter-local specifics
