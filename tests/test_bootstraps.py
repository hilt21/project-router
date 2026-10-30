"""Regression checks for installation entries and their channel dependencies."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from router import core


ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "build", "*.egg-info"))
        self.path = self.root / "bootstrap/interactive-reading.md"

    def tearDown(self):
        self.temp.cleanup()

    def edit_channel(self, edit):
        channel = self.root / "channels/reading-preview.json"
        record = json.loads(channel.read_text())
        edit(record)
        channel.write_text(json.dumps(record))
        (self.root / f"releases/{record['version']}.json").write_text(json.dumps(record))

    def test_all_entries_resolve_to_their_declared_project(self):
        results = core.validate_bootstraps(self.root)
        self.assertEqual({r["project_id"] for r in results}, set(core.config(self.root)["routes"]))
        reading = next(r for r in results if r["project_id"] == "interactive-reading")
        self.assertEqual(reading["channel"], "reading-preview")

    def test_missing_reading_channel_fails_full_validation_without_fallback(self):
        (self.root / "channels/reading-preview.json").unlink()
        with self.assertRaisesRegex(core.RouterError, "Missing file: channels/reading-preview.json"):
            core.validate(self.root)
        self.assertTrue((self.root / "channels/stable.json").is_file())

    def test_channel_without_project_route_fails(self):
        self.edit_channel(lambda r: r.update(routes={"new-project": "routes/new-project.md"}))
        with self.assertRaisesRegex(core.RouterError, "does not publish project route"):
            core.validate_bootstraps(self.root)

    def test_wrong_project_route_path_fails(self):
        self.edit_channel(lambda r: r.update(routes={"interactive-reading": "routes/new-project.md"}))
        with self.assertRaisesRegex(core.RouterError, "does not publish project route"):
            core.validate_bootstraps(self.root)

    def test_missing_release_record_fails(self):
        record = json.loads((self.root / "channels/reading-preview.json").read_text())
        (self.root / f"releases/{record['version']}.json").unlink()
        with self.assertRaisesRegex(core.RouterError, "Missing file: releases/"):
            core.validate_bootstraps(self.root)

    def test_invalid_source_sha_fails(self):
        self.edit_channel(lambda r: r.update(commit_sha="unknown"))
        with self.assertRaisesRegex(core.RouterError, "immutable SHA"):
            core.validate_bootstraps(self.root)

    def test_missing_metadata_cannot_hide_the_channel_reference(self):
        self.path.write_text(self.path.read_text().split("---\n", 2)[2])
        with self.assertRaisesRegex(core.RouterError, "Missing frontmatter"):
            core.validate_bootstraps(self.root)

    def test_metadata_and_copyable_body_must_agree(self):
        self.path.write_text(self.path.read_text().replace("channels/reading-preview.json", "channels/stable.json"))
        with self.assertRaisesRegex(core.RouterError, "body channel mismatch"):
            core.validate_bootstraps(self.root)

    def test_body_and_declared_identity_must_agree(self):
        self.path.write_text(self.path.read_text().replace("项目 ID：interactive-reading。", "项目 ID：new-project。"))
        with self.assertRaisesRegex(core.RouterError, "body identity mismatch"):
            core.validate_bootstraps(self.root)

    def test_foreign_repository_is_rejected(self):
        self.path.write_text(self.path.read_text().replace("repository: hilt21/project-router", "repository: other/repo"))
        with self.assertRaisesRegex(core.RouterError, "repository mismatch"):
            core.validate_bootstraps(self.root)

    def test_unknown_project_is_rejected(self):
        self.path.write_text(self.path.read_text().replace("project_id: interactive-reading", "project_id: unknown-project"))
        with self.assertRaisesRegex(core.RouterError, "Unknown bootstrap project"):
            core.validate_bootstraps(self.root)

    def test_duplicate_project_entry_is_rejected(self):
        (self.root / "bootstrap/reading-copy.md").write_text(self.path.read_text())
        with self.assertRaisesRegex(core.RouterError, "Duplicate bootstrap project"):
            core.validate_bootstraps(self.root)


if __name__ == "__main__":
    unittest.main()
