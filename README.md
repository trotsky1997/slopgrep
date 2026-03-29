# slopgrep

`slopgrep` is a semgrep-like scanner for AI writing tells in prose.

It scans text files for regex-based patterns associated with LLM-style writing:
- inflated significance and vague grandiosity
- promotional or listicle-like phrasing
- chatbot artifacts and hedging
- em-dash addiction, bold-first bullets, unicode decoration
- English and Chinese AI-writing tropes

It only scans. It does not rewrite or auto-fix text.

## Quick start

```bash
python -m slopgrep scan .
python -m slopgrep scan docs --json
python -m slopgrep rules
uvx --from . slopgrep rules
```

## Install / run

No external dependencies are required.

```bash
python -m slopgrep scan .
uvx --from . slopgrep scan .
```

After publishing to GitHub, you can run it without cloning:

```bash
uvx --from git+https://github.com/trotsky1997/slopgrep slopgrep rules
uvx --from git+https://github.com/trotsky1997/slopgrep slopgrep scan path/to/text
```

## Commands

### `scan`

Scan one or more files or directories.

```bash
python -m slopgrep scan content/
python -m slopgrep scan README.md docs/ --json
python -m slopgrep scan . --config my-rules.toml
```

Options:
- `--config PATH`: load a custom TOML rule pack
- `--json`: output JSON
- `--include GLOB`: include file glob, repeatable
- `--exclude GLOB`: exclude file glob, repeatable
- `--threshold N`: minimum score for reporting a file summary
- `--max-findings N`: cap findings per file

### `rules`

List built-in rules.

```bash
python -m slopgrep rules
python -m slopgrep rules --json
```

## Rule format

Custom rules are loaded from TOML. Example:

```toml
[[rules]]
id = "custom.phrase"
language = "generic"
message = "Suspicious phrase"
severity = "warning"
pattern = "(?i)\\bhere's the thing\\b"
description = "Teacher-mode transition often found in AI prose"
category = "tone"
weight = 2
```

## Output

Text output is semgrep-inspired:

```text
path/to/file.md:12:1 warning ai.transition.kicker Here's the thing / Here's the kicker transition
  Here's the thing: the market changed.
```

Each file also gets a slop score derived from matched rule weights and repeated trope density.

## Built-in coverage

The built-in rule set includes patterns derived from:
- the Humanizer and Humanizer-ZH guides
- the `tropes.md` gist supplied in this session

## License

MIT
