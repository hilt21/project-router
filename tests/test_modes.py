"""Exercise mode-scoped dependency graphs independently of academic prompts."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from router import core


class ModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(Path(__file__).resolve().parents[1], self.root,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "build", "*.egg-info"))
        cfg = core.config(self.root)
        cfg["routes"]["stage-demo"] = "routes/stage-demo.md"
        (self.root / "project-router.yaml").write_text(yaml.safe_dump(cfg))
        self.route = {
            "schema_version": 2, "id": "stage-demo", "title": "Stages",
            "skills": [], "rules": [], "modes": ["intake", "math", "literature"],
            "default_mode": "intake", "needs_input_modes": ["intake"],
            "required_capabilities": ["github-read"],
            "mode_config": {
                "intake": {},
                "math": {"includes": ["workflows/math-test.md"], "optional_capabilities": ["image-generation"]},
                "literature": {"skills": ["research-open-source"]},
            },
        }
        self.write_route()
        (self.root / "workflows/math-test.md").write_text(
            "---\nproject_id: stage-demo\nincludes: []\nskills: [verify-delivery]\n---\nCheck the proof.\n")

    def tearDown(self):
        self.temp.cleanup()

    def write_route(self):
        (self.root / "routes/stage-demo.md").write_text("---\n" + yaml.safe_dump(self.route) + "---\nStage router.\n")

    def plan(self, mode=None, capabilities=("github-read",)):
        return core.plan(self.root, "stage-demo", "LinkedIn 微信", list(capabilities), mode)

    def test_declared_default_is_not_a_channel_heuristic(self):
        result = self.plan()
        self.assertEqual((result["mode"], result["status"]), ("intake", "needs-input"))
        self.assertEqual(result["skills"], [])

    def test_explicit_stage_loads_only_its_dependencies(self):
        result = self.plan("math")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["skills"], [{"id": "verify-delivery", "activation": "document"}])
        self.assertIn("workflows/math-test.md", [d["path"] for d in result["documents"]])
        self.assertNotIn("skills/research-open-source/SKILL.md", [d["path"] for d in result["documents"]])
        self.assertFalse(result["mutations_authorized"])

    def test_required_tools_include_selected_transitive_skills(self):
        result = self.plan("literature")
        self.assertEqual(result["missing_capabilities"], ["web-search"])
        self.assertEqual(result["status"], "blocked")

    def test_optional_tool_absence_is_visible_without_blocking(self):
        result = self.plan("math")
        self.assertEqual(result["missing_optional_capabilities"], ["image-generation"])
        result = self.plan("math", ["github-read", "image-generation"])
        self.assertEqual(result["missing_optional_capabilities"], [])

    def test_missing_required_tool_blocks_intake(self):
        self.assertEqual(self.plan(capabilities=[])["status"], "blocked")

    def test_unknown_explicit_mode_fails(self):
        with self.assertRaisesRegex(core.RouterError, "Unsupported mode"):
            self.plan("linkedin")

    def test_validator_checks_inactive_mode_paths(self):
        self.route["mode_config"]["math"]["includes"] = ["workflows/missing.md"]
        self.write_route()
        self.assertEqual(self.plan()["status"], "needs-input")
        with self.assertRaisesRegex(core.RouterError, "Missing file"):
            core.validate(self.root)

    def test_mode_specific_cycle_is_rejected(self):
        self.route["mode_config"]["math"]["includes"] = ["routes/stage-demo.md"]
        self.write_route()
        with self.assertRaisesRegex(core.RouterError, "Instruction cycle"):
            self.plan("math")

    def test_cross_project_dependency_is_rejected(self):
        self.route["mode_config"]["math"]["includes"] = ["workflows/content.md"]
        self.write_route()
        with self.assertRaisesRegex(core.RouterError, "Cross-project workflow"):
            self.plan("math")

    def test_profiles_must_cover_declared_modes(self):
        del self.route["mode_config"]["math"]
        self.write_route()
        with self.assertRaisesRegex(core.RouterError, "cover exactly"):
            self.plan()

    def test_unknown_profile_keys_are_rejected(self):
        self.route["mode_config"]["math"]["skill"] = ["verify-delivery"]
        self.write_route()
        with self.assertRaisesRegex(core.RouterError, "Invalid mode configuration"):
            self.plan()

    def test_unknown_capability_in_inactive_profile_is_rejected(self):
        self.route["mode_config"]["math"]["required_capabilities"] = ["admin"]
        self.write_route()
        with self.assertRaisesRegex(core.RouterError, "Unknown instruction capability"):
            core.validate(self.root)

    def test_legacy_schema_cannot_silently_ignore_profiles(self):
        self.route["schema_version"] = 1
        self.write_route()
        with self.assertRaisesRegex(core.RouterError, "requires route schema 2"):
            self.plan()

    def test_budget_includes_packet_metadata(self):
        result = self.plan("math")
        body_bytes = sum(len(core.read_text(self.root, d["path"]).encode()) for d in result["documents"])
        cfg = core.config(self.root)
        cfg["max_packet_bytes"] = body_bytes + 100
        (self.root / "project-router.yaml").write_text(yaml.safe_dump(cfg))
        with self.assertRaisesRegex(core.RouterError, "byte budget"):
            core.packet(self.root, self.plan("math"))


if __name__ == "__main__":
    unittest.main()
