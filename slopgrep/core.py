from __future__ import annotations

from dataclasses import dataclass, asdict, field
from importlib import resources
from pathlib import Path
import fnmatch
import json
import math
import re
import tomllib
from typing import Iterable

EN_STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "they",
    "them",
    "their",
    "there",
    "about",
    "into",
    "while",
    "where",
    "which",
    "have",
    "has",
    "had",
    "will",
    "would",
    "could",
    "should",
    "because",
    "through",
    "these",
    "those",
    "such",
    "than",
    "then",
    "also",
    "very",
    "more",
    "most",
    "only",
}

EN_ABSTRACT_TERMS = {
    "comprehensive",
    "foundational",
    "nuanced",
    "landscape",
    "framework",
    "dynamic",
    "transformative",
    "meaningful",
    "professional",
    "facilitate",
    "demonstrate",
    "utilize",
    "critical",
    "important",
    "structure",
    "system",
    "process",
    "coordination",
    "quality",
    "strategy",
    "value",
    "outcomes",
}

EN_CONCRETE_TERMS = {
    "door",
    "knife",
    "sock",
    "road",
    "pan",
    "table",
    "window",
    "spiderweb",
    "silk",
    "tomato",
    "bolt",
    "deadbolt",
    "kitchen",
    "forest",
    "hand",
    "fingertips",
    "smell",
    "sound",
    "dust",
    "rain",
}

TROPE_FAMILIES = {
    "teacher_mode_en": {
        "terms": ["unpack", "break down", "walk through", "step by step", "understand why", "basics", "at its core"],
        "category": "tone",
        "message": "BM25 family match: teacher-mode explainer",
    },
    "safe_tone_en": {
        "terms": ["appropriate", "effective", "supportive", "responsible", "meaningful", "valuable", "best practices", "value-driven", "dependable", "aligned"],
        "category": "tone",
        "message": "BM25 family match: sanitized safe tone",
    },
    "abstract_hype_en": {
        "terms": ["framework", "landscape", "dynamic", "transformative", "foundational", "nuanced", "meaningful", "process", "system", "strategy"],
        "category": "vocabulary",
        "message": "BM25 family match: abstraction-heavy prose",
    },
    "zh_transition": {
        "terms": ["换句话说", "换言之", "归根结底", "总体而言", "由此可见", "值得注意的是", "这也意味着"],
        "category": "tone",
        "message": "BM25 family match: 中文套路化过渡",
    },
    "zh_safe_tone": {
        "terms": ["积极作用", "重要价值", "稳步推进", "持续提升", "有效支撑", "良好效果", "最佳实践", "有序推进"],
        "category": "tone",
        "message": "BM25 family match: 中文平滑汇报腔",
    },
    "zh_abstract": {
        "terms": ["框架", "体系", "机制", "能力", "增强", "路径", "协同", "整合", "优化", "过程"],
        "category": "vocabulary",
        "message": "BM25 family match: 中文抽象概念堆积",
    },
}

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".adoc",
    ".org",
    ".html",
    ".htm",
    ".tex",
    ".wiki",
    ".mediawiki",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".tsv",
    ".log",
}

DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".idea",
    ".pytest_cache",
    "__pycache__",
    ".md",
}


@dataclass
class Rule:
    id: str
    language: str
    message: str
    severity: str
    pattern: str
    description: str
    category: str
    weight: int
    _compiled: re.Pattern[str] | None = field(default=None, init=False, repr=False, compare=False)

    def compile(self) -> re.Pattern[str]:
        if self._compiled is None:
            try:
                self._compiled = re.compile(self.pattern)
            except re.error as exc:
                raise ValueError(f"Invalid regex for rule {self.id}: {exc}") from exc
        return self._compiled


@dataclass
class Finding:
    path: str
    line: int
    column: int
    severity: str
    rule_id: str
    message: str
    match: str
    excerpt: str
    category: str
    weight: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileReport:
    path: str
    score: int
    findings: list[Finding]
    category_scores: dict[str, int]
    family_scores: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "score": self.score,
            "category_scores": self.category_scores,
            "family_scores": self.family_scores,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def load_rules(config_path: str | None = None) -> list[Rule]:
    if config_path:
        raw = Path(config_path).read_text(encoding="utf-8")
    else:
        raw = resources.files("slopgrep").joinpath("default_rules.toml").read_text(encoding="utf-8")
    data = tomllib.loads(raw)
    rules: list[Rule] = []
    for item in data.get("rules", []):
        rule = Rule(**item)
        rule.compile()
        rules.append(rule)
    return rules


def is_text_path(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in {"readme", "license", "copying"}


def should_include(path: Path, includes: list[str], excludes: list[str]) -> bool:
    normalized = path.as_posix()
    parts = set(path.parts)
    if parts & DEFAULT_EXCLUDES:
        return False
    if any(fnmatch.fnmatch(normalized, pattern) for pattern in excludes):
        return False
    if not includes:
        return is_text_path(path)
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in includes)


def iter_files(targets: Iterable[str], includes: list[str], excludes: list[str]) -> Iterable[Path]:
    seen: set[Path] = set()
    for target in targets:
        path = Path(target)
        if path.is_file():
            if should_include(path, includes, excludes):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path
            continue
        if not path.exists():
            continue
        for child in path.rglob("*"):
            if child.is_file() and should_include(child, includes, excludes):
                resolved = child.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield child


def line_col_for_offset(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if last_newline == -1 else offset - last_newline
    return line, column


def excerpt_for_line(text: str, line_number: int) -> str:
    lines = text.splitlines()
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def _english_content_words(sentence: str) -> set[str]:
    words = re.findall(r"[A-Za-z]{4,}", sentence.lower())
    return {word for word in words if word not in EN_STOPWORDS}


def _adjacent_sentence_pairs(text: str) -> list[tuple[str, str]]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return list(zip(sentences, sentences[1:]))


def _english_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _paragraphs(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def _bm25_score(query_terms: list[str], document: str, avgdl: float) -> float:
    doc = document.lower()
    tokens = re.findall(r"\w+", doc)
    dl = max(len(tokens), 1)
    score = 0.0
    k1 = 1.2
    b = 0.75
    for term in query_terms:
        tf = doc.count(term.lower())
        if tf == 0:
            continue
        idf = 1.0
        denom = tf + k1 * (1 - b + b * dl / max(avgdl, 1.0))
        score += idf * (tf * (k1 + 1)) / denom
    return score


def detect_density_signals(text: str) -> tuple[list[Finding], dict[str, int]]:
    findings: list[Finding] = []
    category_scores: dict[str, int] = {}
    em_dash_count = text.count("—")
    if em_dash_count >= 3:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.emdash",
                message=f"Heavy em-dash density ({em_dash_count})",
                match="—",
                excerpt=excerpt_for_line(text, 1),
                category="formatting",
                weight=min(4, em_dash_count // 2),
            )
        )
        category_scores["formatting"] = category_scores.get("formatting", 0) + min(4, em_dash_count // 2)

    bold_first_count = len(re.findall(r"(?m)^\s*[-*]\s+\*\*[^*]+\*\*:?,?", text))
    if bold_first_count >= 3:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.boldfirst",
                message=f"Repeated bold-first bullets ({bold_first_count})",
                match="**bullet**",
                excerpt=excerpt_for_line(text, 1),
                category="formatting",
                weight=min(4, bold_first_count // 2),
            )
        )
        category_scores["formatting"] = category_scores.get("formatting", 0) + min(4, bold_first_count // 2)

    # Cluster weak rhetorical cues instead of overreacting to single phrases.
    transition_markers = re.findall(
        r"(?i)\b(overall|taken together|in other words|at its core|the truth is|the reality is|"
        r"here'?s the thing|here'?s the kicker|let'?s unpack this|let'?s break this down|"
        r"imagine a world where|to understand why|what this means is)\b",
        text,
    )
    if len(transition_markers) >= 3:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.transition-cluster",
                message=f"Dense AI-style transition/signpost cluster ({len(transition_markers)})",
                match=", ".join(transition_markers[:4]),
                excerpt=excerpt_for_line(text, 1),
                category="tone",
                weight=min(4, 1 + len(transition_markers) // 2),
            )
        )
        category_scores["tone"] = category_scores.get("tone", 0) + min(4, 1 + len(transition_markers) // 2)

    zh_transition_markers = re.findall(
        r"(换句话说|归根结底|这也意味着|总体而言|值得注意的是|某种程度上|由此可见|其核心在于|本质上是)",
        text,
    )
    if len(zh_transition_markers) >= 3:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.zh-transition-cluster",
                message=f"Dense Chinese AI-style transition cluster ({len(zh_transition_markers)})",
                match="、".join(zh_transition_markers[:4]),
                excerpt=excerpt_for_line(text, 1),
                category="tone",
                weight=min(4, 1 + len(zh_transition_markers) // 2),
            )
        )
        category_scores["tone"] = category_scores.get("tone", 0) + min(4, 1 + len(zh_transition_markers) // 2)

    abstract_terms = re.findall(
        r"(?i)\b(comprehensive|foundational|nuanced|landscape|framework|dynamic|transformative|meaningful|"
        r"professional|facilitate|demonstrate|utilize|critical|important)\b",
        text,
    )
    if len(abstract_terms) >= 5:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.abstract-cluster",
                message=f"Dense abstract/disembodied wording cluster ({len(abstract_terms)})",
                match=", ".join(abstract_terms[:5]),
                excerpt=excerpt_for_line(text, 1),
                category="vocabulary",
                weight=min(4, len(abstract_terms) // 2),
            )
        )
        category_scores["vocabulary"] = category_scores.get("vocabulary", 0) + min(4, len(abstract_terms) // 2)

    zh_abstract_terms = re.findall(r"(框架|体系|机制|能力|增强|路径|协同|整合|优化)", text)
    if len(zh_abstract_terms) >= 5:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.zh-abstract-cluster",
                message=f"Dense Chinese abstract wording cluster ({len(zh_abstract_terms)})",
                match="、".join(zh_abstract_terms[:5]),
                excerpt=excerpt_for_line(text, 1),
                category="vocabulary",
                weight=min(4, len(zh_abstract_terms) // 2),
            )
        )
        category_scores["vocabulary"] = category_scores.get("vocabulary", 0) + min(4, len(zh_abstract_terms) // 2)

    safe_tone_terms = re.findall(
        r"(?i)\b(vital|crucial|dynamic|professional|meaningful|valuable|appropriate|effective|supportive|"
        r"responsible|thoughtful|important|positive)\b",
        text,
    )
    if len(safe_tone_terms) >= 5:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.safe-tone-cluster",
                message=f"Dense corporate-safe wording cluster ({len(safe_tone_terms)})",
                match=", ".join(safe_tone_terms[:5]),
                excerpt=excerpt_for_line(text, 1),
                category="tone",
                weight=min(4, len(safe_tone_terms) // 2),
            )
        )
        category_scores["tone"] = category_scores.get("tone", 0) + min(4, len(safe_tone_terms) // 2)

    zh_safe_tone_terms = re.findall(r"(积极作用|重要价值|稳步推进|持续提升|有效支撑|良好效果|合理路径)", text)
    if len(zh_safe_tone_terms) >= 3:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.zh-safe-tone-cluster",
                message=f"Dense Chinese safe-tone cluster ({len(zh_safe_tone_terms)})",
                match="、".join(zh_safe_tone_terms[:4]),
                excerpt=excerpt_for_line(text, 1),
                category="tone",
                weight=min(4, 1 + len(zh_safe_tone_terms) // 2),
            )
        )
        category_scores["tone"] = category_scores.get("tone", 0) + min(4, 1 + len(zh_safe_tone_terms) // 2)

    all_en_words = re.findall(r"[A-Za-z]{4,}", text.lower())
    abstract_count = sum(1 for word in all_en_words if word in EN_ABSTRACT_TERMS)
    concrete_count = sum(1 for word in all_en_words if word in EN_CONCRETE_TERMS)
    if abstract_count >= 6 and concrete_count <= 1:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.abstraction-ratio",
                message=f"High abstract-to-concrete wording ratio ({abstract_count}:{concrete_count})",
                match="abstract-heavy low-imagery prose",
                excerpt=excerpt_for_line(text, 1),
                category="vocabulary",
                weight=min(4, abstract_count // 3),
            )
        )
        category_scores["vocabulary"] = category_scores.get("vocabulary", 0) + min(4, abstract_count // 3)

    zh_concrete_terms = {"门", "刀", "袜子", "锅", "桌", "窗", "蜘蛛网", "番茄", "指尖", "灰尘", "雨滴"}
    zh_abstract_count = len(zh_abstract_terms)
    zh_concrete_count = sum(1 for term in zh_concrete_terms if term in text)
    if zh_abstract_count >= 6 and zh_concrete_count == 0:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.zh-abstraction-ratio",
                message=f"High Chinese abstract-to-concrete wording ratio ({zh_abstract_count}:{zh_concrete_count})",
                match="抽象词过密、缺少具象锚点",
                excerpt=excerpt_for_line(text, 1),
                category="vocabulary",
                weight=min(4, zh_abstract_count // 3),
            )
        )
        category_scores["vocabulary"] = category_scores.get("vocabulary", 0) + min(4, zh_abstract_count // 3)

    high_overlap_pairs = 0
    for left, right in _adjacent_sentence_pairs(text):
        left_words = _english_content_words(left)
        right_words = _english_content_words(right)
        if len(left_words) < 3 or len(right_words) < 3:
            continue
        overlap = len(left_words & right_words)
        minimum = min(len(left_words), len(right_words))
        if minimum and overlap / minimum >= 0.5:
            high_overlap_pairs += 1
    if high_overlap_pairs >= 2:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.treadmill-overlap",
                message=f"Adjacent sentences repeat the same content shape ({high_overlap_pairs} overlaps)",
                match="repeated adjacent abstractions",
                excerpt=excerpt_for_line(text, 1),
                category="structure",
                weight=min(4, high_overlap_pairs),
            )
        )
        category_scores["structure"] = category_scores.get("structure", 0) + min(4, high_overlap_pairs)

    zh_treadmill_pairs = 0
    zh_sentences = [part.strip() for part in re.split(r"(?<=[。！？])", text) if part.strip()]
    zh_keywords = {"框架", "体系", "机制", "能力", "增强", "路径", "整合", "优化", "过程", "问题"}
    for left, right in zip(zh_sentences, zh_sentences[1:]):
        left_hits = {word for word in zh_keywords if word in left}
        right_hits = {word for word in zh_keywords if word in right}
        if len(left_hits & right_hits) >= 2:
            zh_treadmill_pairs += 1
    if zh_treadmill_pairs >= 2:
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id="ai.density.zh-treadmill-overlap",
                message=f"Adjacent Chinese sentences restate the same abstract frame ({zh_treadmill_pairs} overlaps)",
                match="重复抽象框架",
                excerpt=excerpt_for_line(text, 1),
                category="structure",
                weight=min(4, zh_treadmill_pairs),
            )
        )
        category_scores["structure"] = category_scores.get("structure", 0) + min(4, zh_treadmill_pairs)

    en_sentences = _english_sentences(text)
    if len(en_sentences) >= 4:
        unique_content_words: set[str] = set()
        total_content_words = 0
        for sentence in en_sentences:
            words = _english_content_words(sentence)
            unique_content_words.update(words)
            total_content_words += len(words)
        if total_content_words >= 16 and len(unique_content_words) / max(total_content_words, 1) <= 0.45:
            findings.append(
                Finding(
                    path="",
                    line=1,
                    column=1,
                    severity="info",
                    rule_id="ai.density.length-over-substance",
                    message=f"Many sentences but low lexical novelty ({len(unique_content_words)}/{total_content_words})",
                    match="low-information long passage",
                    excerpt=excerpt_for_line(text, 1),
                    category="structure",
                    weight=3,
                )
            )
            category_scores["structure"] = category_scores.get("structure", 0) + 3

    if len(zh_sentences) >= 4:
        zh_total_hits = 0
        zh_unique_hits: set[str] = set()
        zh_keywords = {"框架", "体系", "机制", "能力", "增强", "路径", "整合", "优化", "过程", "问题", "推进", "协同"}
        for sentence in zh_sentences:
            hits = {word for word in zh_keywords if word in sentence}
            zh_unique_hits.update(hits)
            zh_total_hits += len(hits)
        if zh_total_hits >= 8 and len(zh_unique_hits) / max(zh_total_hits, 1) <= 0.5:
            findings.append(
                Finding(
                    path="",
                    line=1,
                    column=1,
                    severity="info",
                    rule_id="ai.density.zh-length-over-substance",
                    message=f"Many Chinese sentences but low abstract-keyword novelty ({len(zh_unique_hits)}/{zh_total_hits})",
                    match="低信息密度长段落",
                    excerpt=excerpt_for_line(text, 1),
                    category="structure",
                    weight=3,
                )
            )
            category_scores["structure"] = category_scores.get("structure", 0) + 3

    paragraphs = _paragraphs(text)
    avgdl = sum(max(len(re.findall(r"\w+", p.lower())), 1) for p in paragraphs) / max(len(paragraphs), 1)
    for name, family in TROPE_FAMILIES.items():
        best = 0.0
        for paragraph in paragraphs:
            best = max(best, _bm25_score(family["terms"], paragraph, avgdl))
        if best < 2.2:
            continue
        weight = min(4, max(2, int(math.floor(best))))
        findings.append(
            Finding(
                path="",
                line=1,
                column=1,
                severity="info",
                rule_id=f"ai.semantic.{name}",
                message=f"{family['message']} (score={best:.2f})",
                match=", ".join(family["terms"][:4]),
                excerpt=excerpt_for_line(text, 1),
                category=family["category"],
                weight=weight,
            )
        )
        category_scores[family["category"]] = category_scores.get(family["category"], 0) + weight

    return findings, category_scores


def scan_text(text: str, path: str, rules: list[Rule], max_findings: int) -> FileReport:
    findings: list[Finding] = []
    category_scores: dict[str, int] = {}
    family_scores: dict[str, int] = {}
    for rule in rules:
        pattern = rule.compile()
        for match in pattern.finditer(text):
            line, column = line_col_for_offset(text, match.start())
            finding = Finding(
                path=path,
                line=line,
                column=column,
                severity=rule.severity,
                rule_id=rule.id,
                message=rule.message,
                match=match.group(0),
                excerpt=excerpt_for_line(text, line),
                category=rule.category,
                weight=rule.weight,
            )
            findings.append(finding)
            category_scores[rule.category] = category_scores.get(rule.category, 0) + rule.weight
            if rule.id.startswith("ai.semantic."):
                family = rule.id.removeprefix("ai.semantic.")
                family_scores[family] = family_scores.get(family, 0) + rule.weight
            if len(findings) >= max_findings:
                break
        if len(findings) >= max_findings:
            break

    density_findings, density_scores = detect_density_signals(text)
    for finding in density_findings:
        if len(findings) >= max_findings:
            break
        findings.append(
            Finding(
                path=path,
                line=finding.line,
                column=finding.column,
                severity=finding.severity,
                rule_id=finding.rule_id,
                message=finding.message,
                match=finding.match,
                excerpt=finding.excerpt,
                category=finding.category,
                weight=finding.weight,
            )
        )
        if finding.rule_id.startswith("ai.semantic."):
            family = finding.rule_id.removeprefix("ai.semantic.")
            family_scores[family] = family_scores.get(family, 0) + finding.weight
    for category, score in density_scores.items():
        category_scores[category] = category_scores.get(category, 0) + score

    score = sum(finding.weight for finding in findings)
    return FileReport(path=path, score=score, findings=findings, category_scores=category_scores, family_scores=family_scores)


def scan_paths(
    targets: Iterable[str],
    rules: list[Rule],
    includes: list[str] | None = None,
    excludes: list[str] | None = None,
    max_findings: int = 100,
    threshold: int = 0,
) -> list[FileReport]:
    include_patterns = includes or []
    exclude_patterns = excludes or []
    reports: list[FileReport] = []
    for path in iter_files(targets, include_patterns, exclude_patterns):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        report = scan_text(text, path.as_posix(), rules, max_findings=max_findings)
        if report.findings or report.score >= threshold:
            reports.append(report)
    reports.sort(key=lambda report: (-report.score, report.path))
    return reports


def reports_to_json(reports: list[FileReport]) -> str:
    return json.dumps({"results": [report.to_dict() for report in reports]}, ensure_ascii=False, indent=2)


def format_report_text(reports: list[FileReport], threshold: int = 0) -> str:
    lines: list[str] = []
    for report in reports:
        if report.score < threshold and not report.findings:
            continue
        lines.append(f"{report.path}: slop_score={report.score}")
        if report.family_scores:
            top = sorted(report.family_scores.items(), key=lambda item: (-item[1], item[0]))[:5]
            formatted = ", ".join(f"{name}={score}" for name, score in top)
            lines.append(f"  top_families: {formatted}")
        for finding in report.findings:
            lines.append(
                f"{finding.path}:{finding.line}:{finding.column} {finding.severity} {finding.rule_id} {finding.message}"
            )
            if finding.excerpt:
                lines.append(f"  {finding.excerpt}")
        lines.append("")
    if not lines:
        return "No findings."
    return "\n".join(lines).rstrip()
