import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from router import core, design

ROOT = Path(__file__).resolve().parents[1]
MONO = "visual-plan=单色海报"
REVIEW = "draft-review=channel-draft-review"


class DesignLibraryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "router"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "build", "*.egg-info"))

    def plan(self, *choices, project="content-studio", mode="wechat", generate=False, resources=None):
        return core.plan(self.root, project, "Technical brief", ["web-search", "github-read"],
                         mode, generate, choices, resources)

    def write(self, path, data):
        (self.root / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def relock(self):
        self.write(core.config(self.root)["lockfile"], core.skill_lock(self.root))

    def reseal(self):
        pointer = core.load_json(self.root, design.INDEX)
        base = self.root / design.PACKAGE / pointer["snapshot"]
        pointer["files"] = {p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in base.rglob("*") if p.is_file()}
        self.write(design.INDEX, pointer)
        self.relock()

    def test_review_and_visual_plan_load_selected_resources_without_generation(self):
        result = self.plan(REVIEW, MONO)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["intended_actions"], [])
        self.assertFalse(result["mutations_authorized"])
        selections = result["design_library"]["entries"]
        self.assertEqual([(e["stage"], e["id"]) for e in selections],
                         [("draft-review", "channel-draft-review"), ("visual-plan", "mono-color-editorial")])
        self.assertTrue(any(d["path"].endswith("design-system/recipes.json") for d in selections[1]["documents"]))
        packet = core.packet(self.root, result)
        self.assertIn("technical-specimen", packet)
        self.assertIn("渠道成稿审校", packet)
        self.assertNotIn("Three.js 参考图", packet)
        self.assertFalse(any(d["path"].endswith("index.json") for d in result["documents"]))

    def test_ordinary_content_packet_does_not_load_design_documents(self):
        result = self.plan()
        self.assertNotIn("design_library", result)
        self.assertFalse(any("/design-library/" in item["path"] for item in result["documents"]))

    def test_invalid_style_stage_default_and_combination_fail(self):
        for choice in ("visual-plan=missing", "visual-plan=channel-draft-review", "visual-plan"):
            with self.subTest(choice=choice), self.assertRaisesRegex(core.RouterError, "No design entry"):
                self.plan(choice)
        with self.assertRaisesRegex(core.RouterError, "one entry per configured"):
            self.plan(MONO, MONO)
        with self.assertRaisesRegex(core.RouterError, "one entry per configured"):
            self.plan(MONO, project="new-project", mode="research")
        with self.assertRaisesRegex(core.RouterError, "combination is not configured"):
            self.plan("slide-design=PPT设计", "web-review=网页设计评审", project="new-project", mode="research")
        self.assertEqual(self.plan("draft-review")["status"], "ready")

    def test_five_domains_have_configured_entries(self):
        cases = [("new-project", "research", "slide-design=PPT设计"),
                 ("new-project", "research", "3d-design=Three.js重建"),
                 ("new-project", "research", "web-review=网页设计评审"),
                 ("content-studio", "wechat", MONO), ("content-studio", "linkedin", REVIEW)]
        for project, mode, request in cases:
            with self.subTest(request=request):
                result = self.plan(request, project=project, mode=mode)
                self.assertEqual(result["status"], "ready")
                self.assertEqual(len(result["design_library"]["entries"]), 1)

    def test_image_action_and_host_capability_are_separate(self):
        with self.assertRaisesRegex(core.RouterError, "needs --generate-images"):
            self.plan("image-generation=mono-color")
        result = self.plan("image-generation=mono-color", generate=True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("image-generation", result["missing_capabilities"])

    def test_optional_data_is_loaded_only_when_selected(self):
        resource = "mono-color-editorial=design-system/colors.json"
        result = self.plan(MONO, resources=[resource])
        self.assertTrue(any(d["path"].endswith("colors.json") for d in result["documents"]))
        self.assertFalse(any(d["path"].endswith("colors.json") for d in self.plan(MONO)["documents"]))
        for choices, resources in [((), [resource]), ((REVIEW,), [resource]),
                                   ((MONO,), ["mono-color-editorial=../secret.txt"])]:
            with self.subTest(resources=resources), self.assertRaises(core.RouterError):
                self.plan(*choices, resources=resources)

    def test_catalog_growth_does_not_inflate_selected_packet(self):
        before = core.packet(self.root, self.plan(MONO))
        pointer = core.load_json(self.root, design.INDEX)
        base = self.root / design.PACKAGE / pointer["snapshot"]
        consumer = core.load_json(self.root, design.BINDINGS)
        original = core.load_json(self.root, f"{design.PACKAGE}/{pointer['snapshot']}/manifests/mono-color-editorial.json")
        for n in range(12):
            eid = f"extra-style-{n}"
            folder = base / "entries" / eid
            folder.mkdir()
            content = f"# Style {n}\n".encode()
            (folder / "SKILL.md").write_bytes(content)
            files = {"SKILL.md": design.digest(content)}
            manifest = {**original, "id": eid, "aliases": [], "required": [], "resources": {},
                        "files": files, "content_sha256": design.files_digest(files)}
            (base / "manifests" / f"{eid}.json").write_text(json.dumps(manifest))
            pointer["entries"].append(eid)
            consumer["projects"]["content-studio"]["stages"]["visual-plan"]["entries"].append(eid)
        self.write(design.INDEX, pointer)
        self.write(design.BINDINGS, consumer)
        self.reseal()
        self.assertEqual(before, core.packet(self.root, self.plan(MONO)))
        self.assertEqual(self.plan("visual-plan=extra-style-11")["design_library"]["entries"][0]["id"], "extra-style-11")

    def test_binding_to_another_project_needs_only_configuration(self):
        consumer = core.load_json(self.root, design.BINDINGS)
        consumer["projects"]["new-project"]["stages"]["visual-plan"] = {"entries": ["mono-color-editorial"]}
        self.write(design.BINDINGS, consumer)
        self.assertEqual(self.plan(MONO, project="new-project", mode="research")["status"], "ready")

    def test_combined_packet_budget_is_validated_before_ready(self):
        single = max(len(core.packet(self.root, self.plan(request)).encode()) for request in (REVIEW, MONO))
        combined = len(core.packet(self.root, self.plan(REVIEW, MONO)).encode())
        self.assertGreater(combined, single)
        config_file = self.root / "project-router.yaml"
        config_file.write_text(config_file.read_text().replace("max_packet_bytes: 40000", f"max_packet_bytes: {single}"))
        self.plan(REVIEW)
        self.plan(MONO)
        with self.assertRaisesRegex(core.RouterError, "Execution packet exceeds byte budget"):
            self.plan(REVIEW, MONO)
        with self.assertRaisesRegex(core.RouterError, "byte budget"):
            core.validate(self.root)

    def test_source_drift_is_not_hidden_by_relocking(self):
        selection = self.plan(MONO)["design_library"]["entries"][0]
        (self.root / selection["documents"][0]["path"]).write_text("unexpected edit")
        self.relock()
        with self.assertRaisesRegex(core.RouterError, "snapshot file drift"):
            self.plan(MONO)

    def make_receipt(self):
        for args in [("init", "-q"), ("config", "user.email", "test@example.invalid"),
                     ("config", "user.name", "Test"), ("add", "."), ("commit", "-qm", "fixture")]:
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)
        result = self.plan(REVIEW, MONO)
        artifact_root = self.root.parent / "artifacts"
        artifact_root.mkdir()
        output = artifact_root / "cover-plan.json"
        output.write_text('{"stage":"visual-plan"}\n')
        receipt = core.load_json(self.root, "templates/receipt.example.json")
        receipt.update(project_id="content-studio", mode="wechat", snapshot_sha=result["source"]["sha"],
                       status="complete", design_library=result["design_library"],
                       source_readback=[{**d, "tool": "local-file-read"} for d in result["documents"]],
                       artifacts=[{"path": output.name, "sha256": design.digest(output.read_bytes())}],
                       verification=[{"check": "fixture bytes", "status": "passed", "kind": "artifact-check", "evidence": [output.name]}])
        return receipt, artifact_root

    def test_receipt_checks_version_readback_and_artifact_bytes(self):
        receipt, artifacts = self.make_receipt()
        self.assertEqual(core.validate_receipt(receipt, self.root, artifacts)["status"], "passed")
        mutations = [lambda d: d["design_library"].update(commit_sha="b" * 40),
                     lambda d: d.update(snapshot_sha="b" * 40),
                     lambda d: d["design_library"]["entries"][0].update(content_sha256="b" * 64),
                     lambda d: d["source_readback"].clear(), lambda d: d["artifacts"].clear()]
        for mutate in mutations:
            changed = copy.deepcopy(receipt)
            mutate(changed)
            with self.assertRaises(core.RouterError): core.validate_receipt(changed, self.root, artifacts)
        with self.assertRaisesRegex(core.RouterError, "artifact-root"):
            core.validate_receipt(receipt, self.root)
        (artifacts / "cover-plan.json").write_text("tampered output")
        with self.assertRaisesRegex(core.RouterError, "artifact digest mismatch"):
            core.validate_receipt(receipt, self.root, artifacts)

    def test_partial_receipt_accepts_missing_readback_but_rejects_wrong_hashes(self):
        receipt, artifacts = self.make_receipt()
        receipt.update(status="partial", artifacts=[])
        path = receipt["design_library"]["entries"][0]["documents"][0]["path"]
        receipt["source_readback"] = [d for d in receipt["source_readback"] if d["path"] != path]
        self.assertEqual(core.validate_receipt(receipt, self.root, artifacts)["status"], "passed")
        receipt["source_readback"].append({"path": path, "sha256": "b" * 64, "tool": "fixture"})
        with self.assertRaisesRegex(core.RouterError, "matching source readback"):
            core.validate_receipt(receipt, self.root, artifacts)

    def test_malformed_receipt_entries_and_artifact_paths_fail(self):
        receipt, artifacts = self.make_receipt()
        mutations = [lambda d: d["design_library"].update(entries=[None]),
                     lambda d: d.update(mode="missing-mode"),
                     lambda d: d["artifacts"][0].update(path="../outside"),
                     lambda d: d["artifacts"][0].pop("path")]
        for mutate in mutations:
            changed = copy.deepcopy(receipt)
            mutate(changed)
            with self.assertRaises(core.RouterError):
                core.validate_receipt(changed, self.root, artifacts)


if __name__ == "__main__":
    unittest.main()
