# Dissertation chapters slopgrep report

Scan target: `/mnt/c/Users/trots/Documents/phd_dissertation/docs/chapters`

Command used:

```bash
python3 -m slopgrep scan /mnt/c/Users/trots/Documents/phd_dissertation/docs/chapters \
  --include '*.tex' --include '*.md' --include '*.txt' --json
```

This report emphasizes writing-style findings and downweights obvious LaTeX / typography noise. The following rules were treated as formatting-heavy and filtered from the ranking summary:

- `ai.unicode.decoration`
- `ai.emdash.addiction`
- `ai.density.emdash`
- `ai.density.boldfirst`

## Overall read

- The dissertation does not look like pasted chatbot output.
- The main recurring signal is not chatbot residue but abstract academic smoothing: repeated use of `框架 / 体系 / 机制 / 能力 / 增强 / 路径 / 优化`.
- The most common semantic family is `zh_abstract`, which means the scanner repeatedly sees passages that resemble abstract concept stacking more than direct concrete exposition.
- After filtering formatting noise, the highest-priority files are `chapter1_domain_lm.tex`, `introduction.tex`, `conclusion.tex`, `appendix_experiments.tex`, and `related_work.tex`.

## Priority ranking

### 1. `chapter1_domain_lm.tex`

- Raw score: 124
- Filtered score: 80
- Top categories: `structure=39`, `vocabulary=29`, `tone=12`
- Top family: `zh_abstract=4`

Why it ranks high:
- The file still scores high even after stripping formatting noise.
- The main issue is not typography; it is repeated abstract framing and repeated conceptual restatement.
- `ai.abstraction.disembodied` appears early, followed by many `ai.zh.vocab` matches.

What that means in practice:
- The prose often leans on abstract capability language rather than concrete task or observation language.
- This chapter is a good place to inspect for concept-heavy paraphrase loops.

### 2. `introduction.tex`

- Raw score: 86
- Filtered score: 72
- Top categories: `vocabulary=45`, `structure=23`, `tone=4`
- Top family: `zh_abstract=4`

Why it matters:
- This is the strongest non-formatting signal in the whole thesis front matter.
- It combines heavy abstract vocabulary with visible structural smoothing.
- The introduction is where repeated thesis-level abstractions are most likely to read as AI-smoothed even if they are fully human-authored.

Most likely issue types:
- repeated abstract-noun clusters
- orderly capability-chain summaries
- low-information restatement across nearby sentences

### 3. `conclusion.tex`

- Raw score: 54
- Filtered score: 46
- Top categories: `vocabulary=28`, `structure=15`, `template=3`
- Top family: `zh_abstract=4`

Why it stands out:
- The conclusion naturally concentrates summary language, so it is vulnerable to smoothing and abstraction inflation.
- `ai.zh.challenges` also appears here, suggesting some section framing still looks template-like.

Most likely issue types:
- abstract recap language
- repeated summary of contribution chain
- low-information closing transitions

### 4. `appendix_experiments.tex`

- Raw score: 43
- Filtered score: 32
- Top categories: `vocabulary=25`, `structure=5`, `tone=2`
- Top family: `zh_abstract=3`

Why it matters:
- Even in supplementary material, the writing leans heavily on abstract process and mechanism vocabulary.
- Less likely to be stylistically alarming than the introduction, but still reads concept-dense.

### 5. `related_work.tex`

- Raw score: 49
- Filtered score: 32
- Top categories: `vocabulary=20`, `tone=6`, `analysis=3`, `structure=3`
- Top family: `zh_abstract=4`

Why it matters:
- This file has a meaningful `analysis` component, not just vocabulary accumulation.
- Related work prose often invites broad synthesis, but the scanner sees some passages as over-smoothed and over-abstracted.

### 6. `appendix_cases.tex`

- Raw score: 29
- Filtered score: 23
- Top categories: `vocabulary=18`, `structure=5`
- Top family: `zh_abstract=3`

### 7. `publications.tex`

- Raw score: 22
- Filtered score: 22
- Top categories: `vocabulary=17`, `structure=3`, `tone=2`
- Top family: `zh_abstract=3`

This one is short and structurally repetitive by design, so the result is less worrying.

### 8. `chapter3_agentic_reasoning.tex`

- Raw score: 102
- Filtered score: 10
- Top categories: `vocabulary=7`, `analysis=3`
- Top families: none after filtering

Important note:
- This file looked severe in the raw scan, but almost all of that came from formatting noise.
- After filtering, the writing-style signal is much weaker than the raw score suggests.

## Lower-priority or mostly noisy files

- `chapter2_reasoning_rl.tex`
  - Very high raw score, but dominated by formatting noise in the earlier summary.
- `abbreviations.tex`
  - Mostly ignorable for style review because glossary-like content naturally repeats abstract terms.

## Recurrent signal families

### `zh_abstract`

This is the dominant semantic family across the dissertation. It usually corresponds to repeated presence of words like:

- `框架`
- `体系`
- `机制`
- `能力`
- `增强`
- `路径`
- `协同`
- `整合`
- `优化`
- `过程`

This is not proof of AI writing. In a technical dissertation, these words are legitimate. The issue is density and repetition: when too many adjacent sentences lean on the same abstract bundle, the prose starts to feel smoothed and low in information gain.

## Practical interpretation

The current scan suggests three main risks:

- Abstract concept stacking is denser than it needs to be in several chapters.
- Some paragraphs advance by restating the same conceptual frame rather than adding new concrete information.
- Thesis-level summary sections are especially prone to sounding like polished AI-style synthesis even when the argument itself is real and specific.

## Bottom line

If you want to review only the highest-value files for AI-writing style signals, start here:

1. `chapter1_domain_lm.tex`
2. `introduction.tex`
3. `conclusion.tex`
4. `related_work.tex`
5. `appendix_experiments.tex`

If you want to ignore formatting false positives entirely, do not prioritize files by raw score. Use the filtered view above instead.
