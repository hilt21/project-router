import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from router import core, design


ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = ["web-search"]
MONO = "visual-plan=单色海报"
REVIEW = "draft-review=channel-draft-review"


class DesignLibraryTests(unittest.TestCase):
    def plan(self, *choices, project="content-studio", mode="wechat", generate=False):
        return core.plan(ROOT, project, "Technical brief", CAPABILITIES, mode, generate, choices)

    def test_brief_and_review_select_stage_scoped_documents_without_generation(self):
        result = self.plan(REVIEW, MONO)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["intended_actions"], [])
        self.assertFalse(result["mutations_authorized"])
        selections = result["design_library"]["entries"]
        self.assertEqual([(item["stage"], item["id"]) for item in selections],
                         [("draft-review", "channel-draft-review"),
                          ("visual-plan", "mono-color-editorial")])
        self.assertRegex(result["design_library"]["commit_sha"], r"^[0-9a-f]{40}$")
        self.assertIn("skills/design-library/entries/mono-color-editorial/PROMPT.md",
                      selections[1]["documents"])
        packet = core.packet(ROOT, result)
        self.assertIn("单色海报提示词模板", packet)
        self.assertIn("渠道成稿审校", packet)
        self.assertNotIn("Three.js 参考图", packet)

    def test_ordinary_content_packet_does_not_read_design_files(self):
        result = self.plan()
        self.assertNotIn("design_library", result)
        self.assertFalse(any("/design-library/" in item["path"] for item in result["documents"]))

    def test_missing_style_or_wrong_stage_fails(self):
        for choice in ("visual-plan=missing", "visual-plan=channel-draft-review"):
            with self.subTest(choice=choice), self.assertRaisesRegex(core.RouterError, "No design entry"):
                self.plan(choice)

    def test_duplicate_selection_and_cross_project_use_fail(self):
        with self.assertRaisesRegex(core.RouterError, "one Design Library entry per stage"):
            self.plan(MONO, MONO)
        with self.assertRaisesRegex(core.RouterError, "unavailable for project"):
            self.plan(MONO, project="new-project", mode="research")

    def test_image_generation_needs_explicit_action_and_host_capability(self):
        with self.assertRaisesRegex(core.RouterError, "needs --generate-images"):
            self.plan("image-generation=mono-color")
        result = self.plan("image-generation=mono-color", generate=True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("image-generation", result["missing_capabilities"])

    def test_new_visual_style_is_selected_from_the_index_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / design.PACKAGE
            shutil.copytree(ROOT / design.PACKAGE, package)
            manifest = root / design.INDEX
            index = json.loads(manifest.read_text())
            entry = index["entries"]["mono-color-editorial"]
            path = "entries/grid-editorial/SKILL.md"
            text = b"---\nname: grid-editorial\n---\n# Grid-based cover\n"
            (package / path).parent.mkdir()
            (package / path).write_bytes(text)
            index["entries"]["grid-editorial"] = {
                **entry, "id": "grid-editorial", "entry": path, "dependencies": [],
                "stages": ["visual-plan"], "aliases": ["grid"],
                "files": {path: hashlib.sha256(text).hexdigest()},
            }
            manifest.write_text(json.dumps(index))
            choice, paths, _ = design.select(root, "content-studio", ["visual-plan=grid"], [], False)
            self.assertEqual(choice["entries"][0]["id"], "grid-editorial")
            self.assertIn(f"{design.PACKAGE}/{path}", paths)
            self.assertFalse(any("/mono-color-editorial/" in item for item in paths))
