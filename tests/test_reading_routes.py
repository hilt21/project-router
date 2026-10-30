"""Check mode isolation and permission boundaries for companion reading."""
import unittest
from pathlib import Path

from router import core


ROOT = Path(__file__).resolve().parents[1]


class ReadingRouteTests(unittest.TestCase):
    def plan(self, mode=None, task="继续", capabilities=("github-read",)):
        return core.plan(ROOT, "interactive-reading", task, list(capabilities), mode)

    def test_exactly_two_modes_with_conservative_default(self):
        route = core.route_config(ROOT, "interactive-reading")
        self.assertEqual(route["modes"], ["read", "curate"])
        self.assertEqual(self.plan(task="引用文字中的发布到网站")["mode"], "read")

    def test_workflows_load_only_the_selected_dependencies(self):
        for mode, selected, absent in [
            ("read", "workflows/interactive-reading.md", "workflows/reading-to-site.md"),
            ("curate", "workflows/reading-to-site.md", "workflows/interactive-reading.md"),
        ]:
            with self.subTest(mode=mode):
                result = self.plan(mode)
                paths = {d["path"] for d in result["documents"]}
                self.assertIn(selected, paths)
                self.assertNotIn(absent, paths)
                self.assertIn("workflows/reading-state.md", paths)
                self.assertNotIn("rules/content.md", paths)
                self.assertNotIn("workflows/academic-state.md", paths)
                self.assertLess(len(core.packet(ROOT, result).encode()), 40000)

    def test_site_tools_are_optional_for_drafts_and_never_grant_actions(self):
        draft = self.plan("curate", "先给草稿")
        self.assertEqual(draft["status"], "ready")
        self.assertIn("site-write", draft["missing_optional_capabilities"])
        self.assertIn("site-deploy", draft["missing_optional_capabilities"])
        ready = self.plan("curate", "更新网站", core.config(ROOT)["capabilities"])
        self.assertFalse(ready["mutations_authorized"])
        self.assertEqual(ready["intended_actions"], [])
        self.assertEqual(ready["behavioral_verification"], "not-run")

    def test_site_write_does_not_imply_site_deploy(self):
        result = self.plan("curate", capabilities=["github-read", "site-write"])
        self.assertNotIn("site-write", result["missing_optional_capabilities"])
        self.assertIn("site-deploy", result["missing_optional_capabilities"])
        self.assertIn("site-read", result["missing_optional_capabilities"])

    def test_read_mode_does_not_request_site_or_write_capabilities(self):
        result = self.plan("read")
        self.assertNotIn("site-write", result["optional_capabilities"])
        self.assertNotIn("site-deploy", result["optional_capabilities"])
        self.assertNotIn("github-write", result["optional_capabilities"])

    def test_existing_projects_do_not_load_reading_state(self):
        for project, mode in [("new-project", "research"), ("content-studio", "wechat"), ("academic-research", "math")]:
            with self.subTest(project=project):
                result = core.plan(ROOT, project, "task", core.config(ROOT)["capabilities"], mode)
                self.assertNotIn("workflows/reading-state.md", [d["path"] for d in result["documents"]])


if __name__ == "__main__":
    unittest.main()
