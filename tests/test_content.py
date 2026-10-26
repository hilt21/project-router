"""Check content platform boundaries; semantic quality is reviewed in cloud probes."""
import subprocess
import sys
import unittest
from pathlib import Path

from router import core
from scripts.check_wechat_title import count_title_characters, is_publishable_title

ROOT = Path(__file__).resolve().parents[1]


class ContentTests(unittest.TestCase):
    def plan(self, mode=None, images=False):
        return core.plan(ROOT, "content-studio", "公众号 LinkedIn 先别生图", ["web-search"], mode, images)

    def paths(self, mode):
        return {d["path"] for d in self.plan(mode)["documents"]}

    def test_wechat_does_not_load_linkedin_rules(self):
        paths = self.paths("wechat")
        self.assertIn("rules/content-wechat.md", paths)
        self.assertNotIn("rules/content-linkedin.md", paths)

    def test_linkedin_does_not_load_wechat_rules(self):
        paths = self.paths("linkedin")
        self.assertIn("rules/content-linkedin.md", paths)
        self.assertNotIn("rules/content-wechat.md", paths)

    def test_dual_is_ready_and_shares_one_common_fact_workflow(self):
        result = self.plan("dual")
        paths = [d["path"] for d in result["documents"]]
        self.assertEqual(result["status"], "ready")
        self.assertIn("rules/content-wechat.md", paths)
        self.assertIn("rules/content-linkedin.md", paths)
        self.assertEqual(paths.count("workflows/content.md"), 1)
        self.assertEqual(paths.count("rules/content.md"), 1)

    def test_host_must_resolve_platform_from_context(self):
        result = self.plan()
        self.assertEqual((result["mode"], result["status"]), ("select-channel", "needs-input"))
        self.assertNotIn("rules/content-linkedin.md", self.paths(None))

    def test_visual_brief_does_not_require_or_authorize_generation(self):
        result = self.plan("wechat")
        self.assertEqual(result["missing_capabilities"], [])
        self.assertEqual(result["intended_actions"], [])
        self.assertFalse(result["mutations_authorized"])
        self.assertEqual(self.plan("wechat", images=True)["missing_capabilities"], ["image-generation"])

    def test_non_content_projects_do_not_load_content_rules(self):
        for project, mode in (("new-project", "research"), ("academic-research", "math")):
            paths = core.instruction_paths(ROOT, project, mode)
            self.assertFalse(any(p.startswith("rules/content") for p in paths))

    def test_wechat_title_contract_is_explicit_and_platform_scoped(self):
        wechat = (ROOT / "rules/content-wechat.md").read_text(encoding="utf-8")
        linkedin = (ROOT / "rules/content-linkedin.md").read_text(encoding="utf-8")
        self.assertIn("20 个字符，包含标点", wechat)
        self.assertIn("候选标题、选定标题和发布前最终标题", wechat)
        self.assertIn("scripts/check_wechat_title.py", wechat)
        self.assertNotIn("20 个字符，包含标点", linkedin)

    def test_wechat_title_count_boundary_and_punctuation(self):
        example = "企业AI用户的冰火两重天"
        exactly_twenty = example + "12345678"
        too_long = exactly_twenty + "，"
        self.assertEqual(count_title_characters(example), 12)
        self.assertEqual(count_title_characters(exactly_twenty), 20)
        self.assertEqual(count_title_characters(too_long), 21)
        self.assertTrue(is_publishable_title(exactly_twenty))
        self.assertFalse(is_publishable_title(too_long))
        self.assertFalse(is_publishable_title(""))
        self.assertFalse(is_publishable_title("标题\n第二行"))
        self.assertFalse(is_publishable_title("   "))

    def test_wechat_title_cli_rejects_over_limit_candidate(self):
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "scripts/check_wechat_title.py"),
                "企业AI用户的冰火两重天",
                "企业AI用户的冰火两重天12345678，",
            ],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("PASS 12/20", result.stdout)
        self.assertIn("FAIL 21/20", result.stdout)


if __name__ == "__main__":
    unittest.main()
