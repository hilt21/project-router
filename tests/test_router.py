from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from router import core
from router.cli import main

ROOT = Path(__file__).resolve().parents[1]


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "build", "*.egg-info", ".venv"))
        self.receipt = core.load_json(self.root, "templates/receipt.example.json")

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, path, old, new):
        file = self.root / path
        self.assertIn(old, file.read_text())
        file.write_text(file.read_text().replace(old, new), encoding="utf-8")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True, stderr=subprocess.DEVNULL).strip()

    def test_repository_validates(self):
        self.assertEqual(core.validate(self.root)["skills"], 11)

    def test_legacy_and_academic_route_cases(self):
        result = core.evaluate(self.root)
        self.assertEqual(len(core.load_yaml(self.root, "evals/routing.yaml")["cases"]), 20)
        self.assertEqual(len(result["cases"]), 60)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["behavioral_verification"], "not-run")

    def test_missing_workflow_blocks(self):
        self.edit("routes/new-project.md", "workflows/research.md", "workflows/missing.md")
        with self.assertRaisesRegex(core.RouterError, "Missing file"):
            core.validate(self.root)

    def test_unknown_skill_blocks(self):
        self.edit("routes/new-project.md", "research-open-source", "missing-skill")
        with self.assertRaisesRegex(core.RouterError, "Unknown skill"):
            core.instruction_paths(self.root, "new-project")

    def test_cycle_blocks(self):
        self.edit("rules/shared.md", "includes: []", "includes: [rules/shared.md]")
        with self.assertRaisesRegex(core.RouterError, "Instruction cycle"):
            core.instruction_paths(self.root, "new-project")

    def test_cross_project_workflow_blocks(self):
        self.edit("routes/new-project.md", "workflows/research.md", "workflows/content.md")
        with self.assertRaisesRegex(core.RouterError, "Cross-project workflow"):
            core.validate(self.root)

    def test_cross_project_rule_blocks(self):
        self.edit("rules/research.md", "project_ids: [new-project]", "project_ids: [content-studio]")
        with self.assertRaisesRegex(core.RouterError, "Cross-project rule"):
            core.validate(self.root)

    def test_parent_path_blocks(self):
        with self.assertRaises(core.RouterError):
            core.safe_path(self.root, "../outside.md")

    def test_absolute_path_blocks(self):
        with self.assertRaises(core.RouterError):
            core.safe_path(self.root, "/etc/passwd")

    def test_symlink_blocks(self):
        (self.root / "rules/link.md").symlink_to(self.root / "rules/shared.md")
        with self.assertRaisesRegex(core.RouterError, "Symlink"):
            core.safe_path(self.root, "rules/link.md")

    def test_duplicate_yaml_key_blocks(self):
        with self.assertRaisesRegex(core.RouterError, "Duplicate YAML key"):
            core.parse_yaml("workflow: a\nworkflow: b\n", "example")

    def test_skill_content_drift_blocks(self):
        self.edit("skills/verify-delivery/SKILL.md", "交付证据检查", "交付检查")
        with self.assertRaisesRegex(core.RouterError, "lock mismatch"):
            core.check_lock(self.root)

    def test_added_skill_file_drift_blocks(self):
        (self.root / "skills/verify-delivery/extra.txt").write_text("unexpected")
        with self.assertRaisesRegex(core.RouterError, "lock mismatch"):
            core.check_lock(self.root)

    def test_packet_is_project_scoped(self):
        result = core.plan(self.root, "new-project", "Compare", ["web-search", "github-read"])
        paths = {x["path"] for x in result["documents"]}
        self.assertNotIn("rules/content.md", paths)
        self.assertNotIn("skills/craft-channel-content/SKILL.md", paths)
        self.assertIn("SHA-256:", core.packet(self.root, result))

    def test_missing_tools_do_not_grant_mutations(self):
        result = core.plan(self.root, "new-project", "deploy everything", [])
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["mutations_authorized"])

    def test_explicit_mode_uses_current_context(self):
        result = core.plan(self.root, "content-studio", "继续", ["web-search"], "linkedin")
        self.assertEqual(result["mode"], "linkedin")

    def test_image_mentions_do_not_infer_an_action(self):
        for task in ("公众号先别生图", "为公众号写生图提示词", "WeChat: do not generate images"):
            result = core.plan(self.root, "content-studio", task, ["web-search"], "wechat")
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["intended_actions"], [])
        result = core.plan(self.root, "content-studio", "公众号", ["web-search"], "wechat", generate_images=True)
        self.assertEqual(result["missing_capabilities"], ["image-generation"])

    def test_packet_budget_blocks(self):
        self.edit("project-router.yaml", "max_packet_bytes: 40000", "max_packet_bytes: 10")
        with self.assertRaisesRegex(core.RouterError, "byte budget"):
            core.validate(self.root)

    def test_self_report_cannot_pass(self):
        self.receipt["verification"] = [{"check": "looks good", "status": "passed", "kind": "self-report", "evidence": ["I checked"]}]
        with self.assertRaisesRegex(core.RouterError, "observable evidence"):
            core.validate_receipt(self.receipt)

    def test_empty_evidence_cannot_pass(self):
        self.receipt["verification"][0]["status"] = "passed"
        with self.assertRaisesRegex(core.RouterError, "observable evidence"):
            core.validate_receipt(self.receipt)

    def test_complete_needs_readback(self):
        self.receipt["status"] = "complete"
        with self.assertRaisesRegex(core.RouterError, "source readback"):
            core.validate_receipt(self.receipt)

    def test_unknown_source_stays_unknown(self):
        self.receipt["snapshot_sha"] = None
        self.receipt["status"] = "unknown"
        self.assertEqual(core.validate_receipt(self.receipt)["authenticity"], "not-verified")
        self.receipt["status"] = "complete"
        with self.assertRaisesRegex(core.RouterError, "unknown source"):
            core.validate_receipt(self.receipt)

    def test_secret_pattern_blocks(self):
        self.receipt["unverified"] = ["ghp_" + "a" * 30]
        with self.assertRaisesRegex(core.RouterError, "credential"):
            core.validate_receipt(self.receipt)

    def test_feedback_uses_whitelist(self):
        self.receipt["private_transcript"] = "Do not publish this text"
        body = core.feedback_body(self.receipt, "routing", "Observed a wrong route", "Select the right route", "project")
        self.assertNotIn("Do not publish", body)
        self.assertIn("new-project", body)

    def test_receipt_time_needs_timezone(self):
        self.receipt["created_at"] = "2026-10-24T12:00:00"
        with self.assertRaisesRegex(core.RouterError, "timezone"):
            core.validate_receipt(self.receipt)

    def test_release_and_rollback(self):
        # Offline git integration: real source commits, immutable records, pointer rollback.
        shutil.rmtree(self.root / "channels", ignore_errors=True)
        shutil.rmtree(self.root / "releases", ignore_errors=True)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "source A")
        source_a = self.git("rev-parse", "HEAD")
        core.create_release(self.root, "v0.1.0", source_a)
        core.promote(self.root, "v0.1.0", "stable")
        self.edit("rules/research.md", "调研约束", "调研约束 A")
        with self.assertRaisesRegex(core.RouterError, "differ"):
            core.create_release(self.root, "v0.2.0", source_a)
        self.git("add", ".")
        self.git("commit", "-m", "source B")
        source_b = self.git("rev-parse", "HEAD")
        core.create_release(self.root, "v0.2.0", source_b)
        core.promote(self.root, "v0.2.0", "stable")
        self.assertEqual(core.read_channel(self.root, "stable")["commit_sha"], source_b)
        core.promote(self.root, "v0.1.0", "stable")
        self.assertEqual(core.read_channel(self.root, "stable")["commit_sha"], source_a)
        with self.assertRaisesRegex(core.RouterError, "immutable"):
            core.create_release(self.root, "v0.1.0", source_b)

    def test_modified_channel_record_blocks(self):
        record = {"schema_version": 1, "repository": "hilt21/project-router", "version": "v0.1.0", "commit_sha": "1" * 40, "routes": core.config(self.root)["routes"]}
        (self.root / "channels").mkdir(exist_ok=True)
        (self.root / "releases").mkdir(exist_ok=True)
        (self.root / "releases/v0.1.0.json").write_text(json.dumps(record))
        record["commit_sha"] = "2" * 40
        (self.root / "channels/stable.json").write_text(json.dumps(record))
        with self.assertRaisesRegex(core.RouterError, "differs"):
            core.read_channel(self.root, "stable")

    def test_older_route_map_can_be_promoted(self):
        record = {"schema_version": 1, "repository": "hilt21/project-router", "version": "v0.0.1", "commit_sha": "1" * 40, "routes": {"new-project": "routes/new-project.md"}}
        (self.root / "releases").mkdir(exist_ok=True)
        (self.root / "releases/v0.0.1.json").write_text(json.dumps(record))
        core.promote(self.root, "v0.0.1", "stable")
        self.assertEqual(core.read_channel(self.root, "stable")["routes"], record["routes"])

    def test_release_history_guard(self):
        import importlib.util
        import os
        spec = importlib.util.spec_from_file_location("release_guard", self.root / "scripts/check_release_history.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        shutil.rmtree(self.root / "channels", ignore_errors=True)
        shutil.rmtree(self.root / "releases", ignore_errors=True)
        (self.root / "releases").mkdir()
        record = self.root / "releases/v0.1.0.json"
        record.write_text("{}")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "initial record")
        base = self.git("rev-parse", "HEAD")
        record.write_text('{"modified": true}')
        self.git("add", ".")
        self.git("commit", "-m", "invalid change")
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            self.assertEqual(module.check(base), ["releases/v0.1.0.json"])
        finally:
            os.chdir(previous)

    def test_cli_ready_and_blocked_exit_codes(self):
        from contextlib import redirect_stdout
        from io import StringIO
        with redirect_stdout(StringIO()):
            self.assertEqual(main(["--root", str(self.root), "plan", "--project", "content-studio", "--mode", "wechat", "--task", "微信公众号", "--capability", "web-search"]), 0)
            self.assertEqual(main(["--root", str(self.root), "plan", "--project", "content-studio", "--mode", "wechat", "--task", "微信公众号"]), 2)


if __name__ == "__main__":
    unittest.main()
