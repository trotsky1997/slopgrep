from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from slopgrep.core import format_report_text, load_rules, scan_paths, scan_text


class SlopgrepTests(unittest.TestCase):
    def test_builtin_rule_matches_english_phrase(self) -> None:
        rules = load_rules()
        text = "Here's the kicker. It's not just a tool, it's a revolution in the evolving landscape of AI."
        report = scan_text(text, "sample.md", rules, max_findings=20)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.transition.kicker", ids)
        self.assertIn("ai.parallelism.negative", ids)
        self.assertGreaterEqual(report.score, 5)

    def test_builtin_rule_matches_chinese_phrase(self) -> None:
        rules = load_rules()
        text = "尽管存在这些挑战，这项工作继续蓬勃发展，并彰显了其重要性。"
        report = scan_text(text, "cn.md", rules, max_findings=20)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.zh.challenges", ids)
        self.assertIn("ai.zh.significance", ids)

    def test_density_signal_for_em_dash(self) -> None:
        rules = load_rules()
        text = "One — two — three — four."
        report = scan_text(text, "dash.md", rules, max_findings=20)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.emdash", ids)

    def test_transition_cluster_density_only_triggers_on_multiple_cues(self) -> None:
        rules = load_rules()
        text = "Here's the thing. At its core, this matters. In other words, the truth is simple."
        report = scan_text(text, "cluster.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.transition-cluster", ids)

        single = scan_text("At its core, this matters.", "single.md", rules, max_findings=50)
        single_ids = {finding.rule_id for finding in single.findings}
        self.assertNotIn("ai.density.transition-cluster", single_ids)

    def test_abstract_cluster_and_seesaw_patterns_match(self) -> None:
        rules = load_rules()
        text = (
            "While the framework is comprehensive, it is important to note that the landscape is dynamic. "
            "This may seem precise, but the deeper issue is that the structure remains abstract. "
            "A meaningful professional framework can facilitate transformative outcomes and demonstrate nuanced value. "
            "A responsible and effective approach can provide valuable and supportive outcomes. "
            "He looked at the door, feeling a strong desire to leave the room."
        )
        report = scan_text(text, "abstract.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.equivocation.seesaw", ids)
        self.assertIn("ai.contrast.seems-but", ids)
        self.assertIn("ai.density.abstract-cluster", ids)
        self.assertIn("ai.density.safe-tone-cluster", ids)
        self.assertIn("ai.subtext.explained", ids)

    def test_treadmill_overlap_heuristic_matches(self) -> None:
        rules = load_rules()
        text = (
            "The framework improves coordination and process quality across the system. "
            "The framework improves process quality and coordination across the broader system. "
            "This framework also improves coordination and process quality across the system."
        )
        report = scan_text(text, "treadmill.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.treadmill-overlap", ids)

    def test_abstraction_ratio_and_personified_callback_match(self) -> None:
        rules = load_rules()
        text = (
            "The comprehensive framework supports transformative coordination, dynamic process quality, meaningful strategy, and professional outcomes. "
            "The room remembered the last argument. A soft scent and warm glow filled the scene."
        )
        report = scan_text(text, "imagery.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.abstraction-ratio", ids)
        self.assertIn("ai.personification.callback", ids)
        self.assertIn("ai.sensory.fake", ids)

    def test_length_over_substance_heuristic_matches(self) -> None:
        rules = load_rules()
        text = (
            "The framework improves coordination and process quality across the system. "
            "The framework improves strategy and process quality across the system. "
            "The framework improves coordination and strategic quality across the process. "
            "The framework improves process quality and coordination across the broader system."
        )
        report = scan_text(text, "length.md", rules, max_findings=80)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.length-over-substance", ids)

    def test_semantic_family_scoring_matches(self) -> None:
        rules = load_rules()
        text = "Let's unpack this step by step. At its core, the framework follows best practices and supports a meaningful, effective, value-driven process."
        report = scan_text(text, "semantic.md", rules, max_findings=80)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.semantic.teacher_mode_en", ids)
        self.assertIn("ai.semantic.safe_tone_en", ids)

    def test_rhetoric_patterns_match(self) -> None:
        rules = load_rules()
        text = """Imagine a world where this changes everything.
The result? Chaos.
Not a bug. Not a feature. Just a symptom.
They build features. They build workflows. They build habits.
As an AI language model, I can't directly add content to Wikipedia.
 At its core, this is simple. The first point is speed. The second point is scale. The third point is reach.
 Let's unpack this step by step. Stop. Think again. Start over.
"""
        report = scan_text(text, "artifacts.txt", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.futurism.imagine-world", ids)
        self.assertIn("ai.rhetorical.result-question", ids)
        self.assertIn("ai.rhetorical.just-z", ids)
        self.assertIn("ai.anaphora.repeated-openings", ids)
        self.assertIn("ai.chatbot.refusal", ids)
        self.assertIn("ai.transition.at-its-core", ids)
        self.assertIn("ai.listicle.ordered-prose", ids)
        self.assertIn("ai.teacher.unpack", ids)
        self.assertIn("ai.teacher.step-by-step", ids)
        self.assertIn("ai.fragment.short-punchy", ids)

    def test_chinese_transition_patterns_match(self) -> None:
        rules = load_rules()
        text = "换句话说，这也意味着问题并没有结束。第一，系统需要重构；第二，流程需要调整。归根结底，其核心在于接口设计。某种程度上，不难发现这并不意味着问题已经消失。我们可以先看输入，再看输出。"
        report = scan_text(text, "cn2.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.zh.transition", ids)
        self.assertIn("ai.zh.ordered-prose", ids)
        self.assertIn("ai.zh.abstract-summary", ids)
        self.assertIn("ai.zh.crutch", ids)
        self.assertIn("ai.zh.teacher-mode", ids)
        self.assertIn("ai.density.zh-transition-cluster", ids)

    def test_chinese_abstract_cluster_and_seesaw_match(self) -> None:
        rules = load_rules()
        text = "虽然系统已经优化，但是整体框架、体系、机制与能力增强路径仍需进一步整合。这表面上看很清晰，但更深层的问题在于协同机制并不稳定。该方法具有积极作用、重要价值，并能有效支撑后续工作，实现持续提升与良好效果。"
        report = scan_text(text, "zh-abstract.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.zh.seesaw", ids)
        self.assertIn("ai.zh.contrast", ids)
        self.assertIn("ai.density.zh-abstract-cluster", ids)
        self.assertIn("ai.zh.safe-tone", ids)
        self.assertIn("ai.density.zh-safe-tone-cluster", ids)

    def test_chinese_treadmill_overlap_heuristic_matches(self) -> None:
        rules = load_rules()
        text = "该框架用于能力增强与机制优化。该框架继续围绕能力增强与机制优化展开。该体系最终仍服务于能力增强与机制优化。"
        report = scan_text(text, "zh-treadmill.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.zh-treadmill-overlap", ids)

    def test_chinese_abstraction_ratio_matches(self) -> None:
        rules = load_rules()
        text = "该框架、体系、机制、能力增强路径与协同优化过程共同构成整体方案。这一路径继续围绕能力增强、机制整合与体系优化展开。"
        report = scan_text(text, "zh-ratio.md", rules, max_findings=50)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.zh-abstraction-ratio", ids)

    def test_chinese_length_over_substance_heuristic_matches(self) -> None:
        rules = load_rules()
        text = "该框架围绕能力增强与机制优化展开。该体系继续围绕能力增强与机制优化推进。该路径仍然服务于能力增强与机制优化过程。该方案最终回到能力增强与机制优化问题。"
        report = scan_text(text, "zh-length.md", rules, max_findings=80)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.density.zh-length-over-substance", ids)

    def test_chinese_semantic_family_scoring_matches(self) -> None:
        rules = load_rules()
        text = "换句话说，这也意味着整体框架与体系需要继续优化。总体而言，由此可见该方案能够有效支撑后续工作，并实现持续提升与有序推进。"
        report = scan_text(text, "zh-semantic.md", rules, max_findings=80)
        ids = {finding.rule_id for finding in report.findings}
        self.assertIn("ai.semantic.zh_transition", ids)
        self.assertIn("ai.semantic.zh_safe_tone", ids)

    def test_text_formatter_mentions_score(self) -> None:
        rules = load_rules()
        report = scan_text("I hope this helps! Here's the thing.", "demo.md", rules, max_findings=20)
        output = format_report_text([report])
        self.assertIn("slop_score=", output)
        self.assertIn("ai.chatbot.artifact", output)

    def test_cli_json_output_with_custom_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cfg = tmp_path / "rules.toml"
            cfg.write_text(
                """
[[rules]]
id = "custom.test"
language = "generic"
message = "matched custom phrase"
severity = "warning"
pattern = "(?i)magic phrase"
description = "test rule"
category = "custom"
weight = 5
""".strip(),
                encoding="utf-8",
            )
            sample = tmp_path / "sample.md"
            sample.write_text("This has a magic phrase in it.", encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, "-m", "slopgrep", "scan", str(sample), "--config", str(cfg), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            data = json.loads(proc.stdout)
            self.assertEqual(data["results"][0]["findings"][0]["rule_id"], "custom.test")

    def test_invalid_custom_rule_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cfg = tmp_path / "bad-rules.toml"
            cfg.write_text(
                """
[[rules]]
id = "custom.bad"
language = "generic"
message = "broken regex"
severity = "warning"
pattern = "(unclosed"
description = "test rule"
category = "custom"
weight = 1
""".strip(),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, "-m", "slopgrep", "rules", "--config", str(cfg)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("Invalid regex for rule custom.bad", proc.stderr)

    def test_scan_paths_include_exclude_and_deduplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "keep.md"
            skip = root / "skip.txt"
            keep.write_text("Here's the kicker.", encoding="utf-8")
            skip.write_text("Here's the kicker.", encoding="utf-8")
            rules = load_rules()
            reports = scan_paths(
                [str(root), str(keep)],
                rules,
                includes=["*.md", "*.txt"],
                excludes=["*skip.txt"],
                max_findings=20,
            )
            self.assertEqual(len(reports), 1)
            self.assertEqual(Path(reports[0].path).name, "keep.md")

    def test_scan_paths_skips_non_utf8_and_missing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.txt"
            bad.write_bytes(b"\xff\xfe\x00\x00")
            rules = load_rules()
            reports = scan_paths([str(root), str(root / "missing.txt")], rules, max_findings=20)
            self.assertEqual(reports, [])


if __name__ == "__main__":
    unittest.main()
