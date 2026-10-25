import unittest
from pathlib import Path

from router import core


ROOT = Path(__file__).resolve().parents[1]


class AcademicRouteTests(unittest.TestCase):
    def test_each_stage_loads_one_domain_skill(self):
        stage_skills = {
            "scope": "scope-academic-research", "literature": "build-literature-evidence",
            "math": "audit-mathematical-rigor", "experiment": "validate-research-experiments",
            "write": "write-academic-manuscript", "review": "review-academic-manuscript",
            "submission": "audit-publication-readiness",
        }
        for stage, skill in stage_skills.items():
            with self.subTest(stage=stage):
                result = core.plan(ROOT, "academic-research", "explicit task", ["github-read", "web-search"], stage)
                self.assertEqual([x["id"] for x in result["skills"]], ["verify-delivery", skill])
                paths = [d["path"] for d in result["documents"]]
                self.assertIn("workflows/academic-state.md", paths)
                self.assertNotIn("rules/content.md", paths)
                for other in set(stage_skills.values()) - {skill}:
                    self.assertNotIn(f"skills/{other}/SKILL.md", paths)
                self.assertLess(len(core.packet(ROOT, result).encode()), 40000)

    def test_pipeline_defers_domain_skills_until_transition(self):
        result = core.plan(ROOT, "academic-research", "whole workflow", ["github-read"], "pipeline")
        self.assertEqual([x["id"] for x in result["skills"]], ["verify-delivery"])
        self.assertFalse(result["mutations_authorized"])

    def test_legacy_projects_do_not_import_research_state_contract(self):
        for project, mode in [("new-project", "research"), ("content-studio", "wechat")]:
            result = core.plan(ROOT, project, "task", ["github-read", "web-search"], mode)
            self.assertNotIn("workflows/academic-state.md", [d["path"] for d in result["documents"]])


if __name__ == "__main__":
    unittest.main()
