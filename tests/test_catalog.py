"""Verify catalog discovery, preservation and instruction isolation at public boundaries."""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from router import catalog, core

REPO_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("collect_skill_stars", REPO_ROOT / "scripts/collect_skill_stars.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(REPO_ROOT, self.root,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "build", "*.egg-info"))

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = catalog.main(["--root", str(self.root), *args])
        return code, json.loads(output.getvalue() or errors.getvalue())

    def test_documented_discovery_scenarios_are_inert(self):
        scenarios = [
            (["--stage", "define", "--query", "PRD"], "matt-to-spec"),
            (["--project", "academic-research", "--query", "数学证明"], "ars-research-reference"),
            (["--stage", "verify", "--query", "上线"], "anthropic-webapp-testing"),
        ]
        before = {p: p.read_bytes() for p in (self.root / catalog.BASE).rglob("*") if p.is_file()}
        for options, expected in scenarios:
            code, data = self.command("find", *options)
            self.assertEqual(code, 0)
            self.assertIn(expected, [x["id"] for x in data["results"]])
            self.assertEqual(data["activation"], "none")
            self.assertEqual(data["host_verification"], "not-run")
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_partial_scan_cannot_replace_good_data(self):
        good = self.root / catalog.BASE / "starred-snapshot.json"
        data = json.loads(good.read_text())
        data["complete"] = False
        partial = Path(self.temp.name) / "partial.json"
        partial.write_text(json.dumps(data))
        before = good.read_bytes(), (self.root / catalog.BASE / "sources.yaml").read_bytes()
        code, result = self.command("import-stars", str(partial))
        self.assertEqual(code, 1)
        self.assertIn("Incomplete", result["error"])
        self.assertEqual(before, (good.read_bytes(), (self.root / catalog.BASE / "sources.yaml").read_bytes()))

    def test_sync_preserves_editorial_fields_and_removed_stars(self):
        path = self.root / catalog.BASE / "sources.yaml"
        sources = yaml.safe_load(path.read_text())
        first = next(iter(sources["sources"]))
        source = sources["sources"][first]
        source["notes"] = "Keep this judgement"
        source["kind"] = "reference"
        path.write_text(yaml.safe_dump(sources, allow_unicode=True))
        data = json.loads((self.root / catalog.BASE / "starred-snapshot.json").read_text())
        data["repositories"] = [r for r in data["repositories"] if r["id"] != source["github_id"]]
        data["count"] -= 1
        data["pagination"]["page_counts"][-1] -= 1
        incoming = Path(self.temp.name) / "new.json"
        incoming.write_text(json.dumps(data))
        self.assertEqual(self.command("import-stars", str(incoming))[0], 0)
        updated = yaml.safe_load(path.read_text())["sources"][first]
        self.assertEqual(updated["notes"], "Keep this judgement")
        self.assertEqual(updated["kind"], "reference")
        self.assertEqual(updated["star_state"], "no-longer-starred")
        self.assertEqual(self.command("render")[0], 0)
        self.assertEqual(self.command("check")[0], 0)

    def test_duplicate_account_and_pagination_errors_do_not_import(self):
        original = json.loads((self.root / catalog.BASE / "starred-snapshot.json").read_text())
        for mutation in ("duplicate", "account", "pages"):
            data = json.loads(json.dumps(original))
            if mutation == "duplicate":
                data["repositories"][1] = data["repositories"][0]
            elif mutation == "account":
                data["username"] = "someone-else"
            else:
                data["pagination"]["terminal_next"] = True
            incoming = Path(self.temp.name) / "invalid.json"
            incoming.write_text(json.dumps(data))
            self.assertEqual(self.command("import-stars", str(incoming))[0], 1)

    def test_repository_rename_keeps_identity_and_historical_readings(self):
        data = json.loads((self.root / catalog.BASE / "starred-snapshot.json").read_text())
        repo = next(r for r in data["repositories"] if r["full_name"] == "mattpocock/skills")
        repo["full_name"] = "mattpocock/renamed-skills"
        incoming = Path(self.temp.name) / "rename.json"
        incoming.write_text(json.dumps(data))
        self.assertEqual(self.command("import-stars", str(incoming))[0], 0)
        code, result = self.command("find", "--query", "PRD")
        self.assertEqual(code, 0)
        matched = next(e for e in result["results"] if e["id"] == "matt-to-spec")
        self.assertEqual(matched["repository"], "mattpocock/renamed-skills")

    def test_snapshot_and_generated_doc_drift_fail(self):
        readme = self.root / catalog.BASE / "README.md"
        readme.write_text(readme.read_text() + "stale\n")
        self.assertEqual(self.command("check")[0], 1)
        self.assertEqual(self.command("render")[0], 0)
        self.assertEqual(self.command("render", "--check")[0], 0)
        sources_path = self.root / catalog.BASE / "sources.yaml"
        sources = yaml.safe_load(sources_path.read_text())
        next(iter(sources["sources"].values()))["upstream"]["archived"] = True
        sources_path.write_text(yaml.safe_dump(sources))
        self.assertEqual(self.command("check")[0], 1)

    def test_reading_drift_and_false_host_pass_fail(self):
        path = self.root / catalog.BASE / "entries.yaml"
        original = yaml.safe_load(path.read_text())
        for field, value in (("commit_sha", "a" * 40), ("host_tests", [{"status": "passed"}])):
            data = json.loads(json.dumps(original))
            next(iter(data["entries"].values()))[field] = value
            path.write_text(yaml.safe_dump(data))
            self.assertEqual(self.command("check")[0], 1)

    def test_catalog_cannot_be_loaded_as_instructions(self):
        path = self.root / "routes/new-project.md"
        meta, body = core.document(self.root, "routes/new-project.md")
        meta["includes"] = ["catalog/skills/README.md"]
        path.write_text("---\n" + yaml.safe_dump(meta) + "---\n" + body)
        with self.assertRaisesRegex(core.RouterError, "Catalog data cannot enter"):
            core.plan(self.root, "new-project", "test", ["github-read", "web-search"])

    def test_candidate_text_never_enters_existing_packet(self):
        result = core.plan(self.root, "new-project", "test", ["github-read", "web-search"])
        packet = core.packet(self.root, result)
        self.assertNotIn("matt-to-spec", packet)
        self.assertFalse(any(x["path"].startswith("catalog/") for x in result["documents"]))

    def test_unknown_project_reports_error(self):
        self.assertEqual(self.command("find", "--project", "unknown")[0], 1)


class CollectorTests(unittest.TestCase):
    def test_unexpected_pagination_host_is_rejected_without_following(self):
        calls = []
        class Response(io.StringIO):
            headers = {"Link": '<https://example.com/stars>; rel="next"'}
        def fetch(request, timeout):
            calls.append(request.full_url)
            return Response("[]")
        result = collector.collect("hilt21", fetch)
        self.assertFalse(result["complete"])
        self.assertEqual(len(calls), 1)

    def test_failed_collection_preserves_last_successful_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "stars.json"
            path.write_text("previous success")
            with patch.object(collector, "collect", return_value={"complete": False, "pages": 1,
                                                                 "count": 100, "error": {"status": 429}}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(collector.main(["--username", "hilt21", "--output", str(path)]), 2)
            self.assertEqual(path.read_text(), "previous success")
            self.assertFalse(json.loads(path.with_suffix(".partial.json").read_text())["complete"])

    def test_collector_follows_next_and_stops_at_terminal_page(self):
        calls = []
        class Response(io.StringIO):
            def __init__(self, data, headers):
                super().__init__(json.dumps(data))
                self.headers = headers
        repo = {"id": 1, "full_name": "owner/skill", "default_branch": "main", "archived": False}
        def fetch(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                return Response([{"repo": repo, "starred_at": "2026-10-27"}], {"Link": '<https://api.github.com/user/123/starred?per_page=100&page=2>; rel="next"'})
            return Response([], {})
        data = collector.collect("hilt21", fetch)
        self.assertTrue(data["complete"])
        self.assertEqual((data["pages"], data["count"]), (2, 1))
        self.assertTrue(calls[1].endswith("page=2"))

    def test_duplicate_between_pages_marks_collection_incomplete(self):
        class Response(io.StringIO):
            headers = {"Link": '<https://api.github.com/user/123/starred?per_page=100&page=2>; rel="next"'}
        repo = {"id": 1, "full_name": "owner/skill", "default_branch": "main", "archived": False}
        def fetch(request, timeout):
            return Response(json.dumps([{"repo": repo, "starred_at": "2026-10-27"}]))
        data = collector.collect("hilt21", fetch)
        self.assertFalse(data["complete"])
        self.assertEqual(data["error"]["kind"], "ValueError")
