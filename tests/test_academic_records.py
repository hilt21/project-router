"""Synthetic research records test provenance mechanics, never paper quality."""
import copy
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from router import core
from router.academic import CHECKS, CLAIM_CHECKS, GLOBAL_CHECKS, check_records
from router.cli import main


class AcademicRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sha = "1" * 40
        self.artifacts = []
        for name in ("draft", "source", "proof", "results", "search"):
            path = self.root / f"{name}.md"
            path.write_text(f"Synthetic {name}. Not a real study.\n")
            self.artifacts.append({"id": name, "path": path.name, "sha256": self.digest(path)})
        self.claims = {
            "schema_version": 1, "research_id": "synthetic-study",
            "coverage": {"semantic_extraction": "unknown", "unregistered_candidates": []},
            "claims": [
                {"id": f"c{i}", "text": f"Synthetic {kind} claim.", "kind": kind, "critical": True,
                 "manuscript": {"artifact_id": "draft", "locator": f"paragraph {i}"},
                 "evidence": [{"artifact_id": evidence, "locator": "section 1"}]}
                for i, (kind, evidence) in enumerate([
                    ("external-fact", "source"), ("mathematical", "proof"),
                    ("experimental", "results"), ("novelty", "search"), ("interpretation", "results")], 1)
            ],
        }
        self.save_json("claims.json", self.claims)
        self.artifacts.append({"id": "claims", "path": "claims.json", "sha256": self.digest(self.root / "claims.json")})
        self.audits = {"schema_version": 1, "research_id": "synthetic-study", "audits": []}
        for i, check in enumerate(sorted(CHECKS), 1):
            targets = [] if check in GLOBAL_CHECKS else [c["id"] for c in self.claims["claims"] if check in CLAIM_CHECKS[c["kind"]]]
            bound = self.claims["claims"] if check in GLOBAL_CHECKS else [c for c in self.claims["claims"] if c["id"] in targets]
            needed = {"claims", "draft"} | {ref["artifact_id"] for c in bound for ref in c["evidence"]}
            self.audits["audits"].append({
                "id": f"a{i}", "check": check, "status": "passed", "kind": "artifact-check", "claim_ids": targets,
                "input_bindings": {a["id"]: a["sha256"] for a in self.artifacts if a["id"] in needed},
                "evidence": [{"artifact_id": "draft", "locator": "synthetic checker witness"}],
                "reason": "Synthetic fixture exercises record consistency only.",
                "blocking_findings": [], "limitations": ["No scientific validity is asserted."], "supersedes": [],
            })
        self.passport = {
            "schema_version": 1, "project_id": "academic-research", "research_id": "synthetic-study",
            "workflow_sha": self.sha, "stage": "submission", "stage_status": "complete",
            "artifacts": self.artifacts, "claim_ledger": "claims", "pending_decisions": [],
            "next_step": "Human author reviews the actual evidence.",
        }
        self.save_audits()

    def tearDown(self):
        self.temp.cleanup()

    def digest(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def save_json(self, path, data):
        (self.root / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def save_audits(self):
        self.save_json("audits.json", self.audits)
        self.passport["audit_ledger"] = {"path": "audits.json", "sha256": self.digest(self.root / "audits.json")}
        self.save_json("passport.json", self.passport)

    def audit(self, check):
        return next(a for a in self.audits["audits"] if a["check"] == check)

    def check(self, submission=True, research_id="synthetic-study", sha=None):
        return check_records(self.root / "passport.json", self.root, research_id, sha or self.sha, submission)

    def test_consistent_records_only_become_eligible_for_human_review(self):
        result = self.check()
        self.assertEqual(result["submission_status"], "eligible-for-human-review")
        self.assertEqual(result["scientific_truth"], "not-verified")
        self.assertEqual(result["semantic_extraction"], "unknown")
        self.assertFalse(result["mutations_authorized"])

    def test_reference_existence_cannot_replace_claim_support(self):
        self.audit("claim-support")["status"] = "unknown"
        self.save_audits()
        result = self.check()
        self.assertEqual(result["stage_status"], "complete")
        self.assertEqual(result["submission_status"], "blocked")
        self.assertIn("missing-current-pass:claim-support:c1", result["blockers"])

    def test_formula_edit_stales_dependent_checks(self):
        (self.root / "proof.md").write_text("Changed equation.\n")
        result = self.check()
        states = {a["check"]: a["validity"] for a in result["audits"]}
        self.assertEqual(states["mathematical-rigor"], "stale")
        self.assertEqual(states["reference-existence"], "current")
        self.assertEqual(result["submission_status"], "blocked")

    def test_updating_manifest_hash_does_not_refresh_audit(self):
        (self.root / "proof.md").write_text("Changed equation.\n")
        next(a for a in self.artifacts if a["id"] == "proof")["sha256"] = self.digest(self.root / "proof.md")
        self.save_audits()
        self.assertIn("audit-stale:" + self.audit("mathematical-rigor")["id"], self.check()["blockers"])

    def test_missing_source_cannot_pass(self):
        (self.root / "source.md").unlink()
        self.assertEqual(self.check()["submission_status"], "blocked")

    def test_cross_research_records_fail_closed(self):
        self.claims["research_id"] = "other-study"
        self.save_json("claims.json", self.claims)
        with self.assertRaisesRegex(core.RouterError, "Research ID mismatch"):
            self.check()

    def test_requested_research_identity_is_checked(self):
        with self.assertRaisesRegex(core.RouterError, "Research ID mismatch"):
            self.check(research_id="other-study")

    def test_original_workflow_snapshot_is_checked(self):
        self.assertIn("workflow-snapshot-mismatch", self.check(sha="2" * 40)["blockers"])

    def test_self_report_cannot_mint_a_pass(self):
        self.audit("mathematical-rigor")["kind"] = "self-report"
        self.save_audits()
        with self.assertRaisesRegex(core.RouterError, "observable evidence"):
            self.check()

    def test_required_evidence_bindings_cannot_be_omitted(self):
        del self.audit("mathematical-rigor")["input_bindings"]["proof"]
        self.save_audits()
        with self.assertRaisesRegex(core.RouterError, "input bindings"):
            self.check()

    def test_blocking_findings_are_incompatible_with_passed(self):
        self.audit("originality")["blocking_findings"] = ["Unresolved source copying."]
        self.save_audits()
        with self.assertRaisesRegex(core.RouterError, "blocking findings"):
            self.check()

    def test_claims_require_their_own_audit_coverage(self):
        self.audit("claim-support")["claim_ids"] = ["c1"]
        self.save_audits()
        self.assertIn("missing-current-pass:claim-support:c5", self.check()["blockers"])

    def test_not_applicable_cannot_skip_a_present_math_claim(self):
        audit = self.audit("mathematical-rigor")
        audit.update(status="not-applicable", reason="No mathematics asserted.", evidence=[])
        self.save_audits()
        self.assertIn("missing-current-pass:mathematical-rigor:c2", self.check()["blockers"])

    def test_unregistered_candidates_block_submission(self):
        self.claims["coverage"]["unregistered_candidates"] = ["Unregistered numerical claim in abstract"]
        self.save_json("claims.json", self.claims)
        self.assertIn("unregistered-claim-candidates", self.check()["blockers"])

    def test_pending_decision_blocks_submission(self):
        self.passport["pending_decisions"] = ["Resolve competing explanation."]
        self.save_audits()
        self.assertIn("pending-research-decisions", self.check()["blockers"])

    def test_new_pass_does_not_hide_unresolved_failure(self):
        original = self.audit("claim-support")
        new = copy.deepcopy(original)
        new["id"] = "a-new"
        original["status"] = "failed"
        self.audits["audits"].append(new)
        self.save_audits()
        self.assertIn("unresolved-audit:" + original["id"], self.check()["blockers"])
        new["supersedes"] = [original["id"]]
        self.save_audits()
        self.assertEqual(self.check()["submission_status"], "eligible-for-human-review")

    def test_superseding_cannot_drop_claim_scope(self):
        old = self.audit("claim-support")
        new = copy.deepcopy(old)
        new.update(id="a-new", claim_ids=["c1"], supersedes=[old["id"]])
        self.audits["audits"].append(new)
        self.save_audits()
        with self.assertRaisesRegex(core.RouterError, "preserve check and claim scope"):
            self.check()

    def test_audit_ledger_edit_requires_updated_manifest(self):
        self.audit("originality")["reason"] = "New review text."
        self.save_json("audits.json", self.audits)
        self.assertIn("audit-ledger-stale", self.check()["blockers"])

    def test_path_escape_and_symlink_are_rejected(self):
        self.artifacts[0]["path"] = "../outside.md"
        self.save_audits()
        with self.assertRaisesRegex(core.RouterError, "Disallowed repository path"):
            self.check()
        self.artifacts[0]["path"] = "link.md"
        (self.root / "link.md").symlink_to(self.root / "draft.md")
        self.save_audits()
        with self.assertRaisesRegex(core.RouterError, "Symlink"):
            self.check()

    def test_checker_is_read_only(self):
        before = {p.name: self.digest(p) for p in self.root.iterdir()}
        self.check()
        after = {p.name: self.digest(p) for p in self.root.iterdir()}
        self.assertEqual(before, after)

    def test_cli_consistency_and_submission_are_distinct(self):
        self.audit("claim-support")["status"] = "not-run"
        self.save_audits()
        args = ["academic-check", str(self.root / "passport.json"), "--research-root", str(self.root),
                "--research-id", "synthetic-study", "--snapshot-sha", self.sha]
        with redirect_stdout(StringIO()):
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args + ["--submission"]), 2)


if __name__ == "__main__":
    unittest.main()
