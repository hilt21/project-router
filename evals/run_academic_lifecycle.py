"""Run an isolated synthetic research lifecycle through fresh CLI processes.

This is a local integration evaluation, not a ChatGPT Work or paper-quality test.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ("coverage", "reference-existence", "claim-support", "mathematical-rigor",
          "experiment-validity", "novelty-scope", "originality", "journal-compliance", "review-resolution")
GLOBAL_CHECKS = {"coverage", "originality", "journal-compliance", "review-resolution"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Study:
    def __init__(self, root, research_id, workflow_sha):
        self.root = root
        root.mkdir()
        (root / "draft.md").write_text("Synthetic study: min x^2 on [-1,1]^2. Claimed unique solution: (0,0).\n")
        (root / "proof.md").write_text("Synthetic flawed argument: a positive semidefinite Hessian implies strict convexity.\n")
        self.claims = {"schema_version": 1, "research_id": research_id,
                       "coverage": {"semantic_extraction": "unknown", "unregistered_candidates": []},
                       "claims": [{"id": "c1", "text": "The minimizer is unique.", "kind": "mathematical", "critical": True,
                                   "manuscript": {"artifact_id": "draft", "locator": "paragraph 1"},
                                   "evidence": [{"artifact_id": "proof", "locator": "paragraph 1"}]}]}
        self.audits = {"schema_version": 1, "research_id": research_id, "audits": []}
        self.passport = {"schema_version": 1, "project_id": "academic-research", "research_id": research_id,
                         "workflow_sha": workflow_sha, "stage": "math", "stage_status": "complete",
                         "artifacts": [], "claim_ledger": "claims", "pending_decisions": [],
                         "next_step": "Resolve the synthetic uniqueness finding."}
        self.artifact_paths = {"draft": "draft.md", "proof": "proof.md", "claims": "claims.json"}
        self.register()

    def register(self):
        write_json(self.root / "claims.json", self.claims)
        self.passport["artifacts"] = [{"id": key, "path": path, "sha256": digest(self.root / path)}
                                      for key, path in self.artifact_paths.items()]
        self.save()

    def save(self):
        write_json(self.root / "audits.json", self.audits)
        self.passport["audit_ledger"] = {"path": "audits.json", "sha256": digest(self.root / "audits.json")}
        write_json(self.root / "passport.json", self.passport)

    def review(self, suffix, include_experiment=False, first_failure=False):
        previous = {a["check"]: a for a in self.audits["audits"]}
        bindings = {a["id"]: a["sha256"] for a in self.passport["artifacts"]}
        for check in CHECKS:
            targets = ["c1"] if check == "mathematical-rigor" else ["c2"] if check == "experiment-validity" and include_experiment else []
            applicable = check in GLOBAL_CHECKS or bool(targets)
            old = previous.get(check)
            row = {"id": check + "-" + suffix, "check": check,
                   "status": "failed" if first_failure and check == "mathematical-rigor" else "passed" if applicable else "not-applicable",
                   "kind": "artifact-check", "claim_ids": targets,
                   "input_bindings": bindings.copy(),
                   "evidence": [{"artifact_id": "proof", "locator": "Synthetic fixture witness"}] if applicable else [],
                   "reason": "Synthetic lifecycle fixture only; no journal or independent scientific review is represented.",
                   "blocking_findings": ["Uniqueness is false in the supplied model."] if first_failure and check == "mathematical-rigor" else [],
                   "limitations": ["Mechanical test states cannot establish actual publication readiness."],
                   "supersedes": [old["id"]] if old else []}
            self.audits["audits"].append(row)
        self.save()


def run():
    pointer = json.loads((ROOT / "channels/preview.json").read_text())
    workflow_sha = pointer["commit_sha"]
    trace = []
    with tempfile.TemporaryDirectory(prefix="router-lifecycle-") as temporary:
        base = Path(temporary)
        study = Study(base / "a", "lifecycle-a", workflow_sha)
        other = Study(base / "b", "lifecycle-b", workflow_sha)

        def check(case_id, expected_exit, expected_submission, *, research_id="lifecycle-a", sha=None, submission=True):
            before = {p.name: digest(p) for p in study.root.iterdir() if p.is_file()}
            args = [sys.executable, "-m", "router", "academic-check", str(study.root / "passport.json"),
                    "--research-root", str(study.root), "--research-id", research_id,
                    "--snapshot-sha", sha or workflow_sha]
            if submission:
                args.append("--submission")
            process = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
            result = json.loads(process.stderr if process.returncode == 1 else process.stdout)
            assert process.returncode == expected_exit, (case_id, process.returncode, result, process.stderr)
            if expected_submission is not None:
                assert result["submission_status"] == expected_submission, (case_id, result)
            after = {p.name: digest(p) for p in study.root.iterdir() if p.is_file()}
            assert before == after, (case_id, "checker changed research files")
            trace.append({"case": case_id, "exit_code": process.returncode, "status": result["status"],
                          "submission_status": result.get("submission_status"), "stage": result.get("stage"),
                          "workflow_sha": result.get("workflow_sha"), "blockers": result.get("blockers", []),
                          "error": result.get("error"), "read_only": True})

        # A complete phase can still contain a blocking research finding.
        study.review("initial", first_failure=True)
        check("initial-math-finding-blocks", 2, "blocked")

        # Editing an artifact must stale the old review, even after re-registering hashes.
        (study.root / "draft.md").write_text("Synthetic corrected study: every (0,y), -1<=y<=1, minimizes x^2.\n")
        (study.root / "proof.md").write_text("For every feasible point x^2>=0, with equality iff x=0. Thus all (0,y), -1<=y<=1, minimize the objective.\n")
        study.claims["claims"][0]["text"] = "All points (0,y), -1<=y<=1, are minimizers."
        study.register()
        check("edited-proof-stales-prior-review", 2, "blocked")
        study.review("corrected")
        check("corrected-current-records", 0, "eligible-for-human-review")

        # Run a small deterministic grid check. It remains a finite sample, not a uniqueness proof.
        grid = [(x, y, x*x) for x in (-1, -0.5, 0, 0.5, 1) for y in (-1, -0.5, 0, 0.5, 1)]
        minimum = min(row[2] for row in grid)
        observed = [(x, y) for x, y, value in grid if value == minimum]
        assert len(observed) == 5
        write_json(study.root / "grid.json", {"synthetic": True, "points": len(grid), "minimum": minimum,
                                             "sample_minimizers": observed, "general_proof": False})
        with (study.root / "draft.md").open("a") as draft:
            draft.write("\nResults: five of the 25 sampled grid points attain zero. This finite sample is not a general proof.\n")
        study.artifact_paths["grid"] = "grid.json"
        study.claims["claims"].append({"id": "c2", "text": "Five grid points attain the minimum among the 25 sampled points.",
                                      "kind": "experimental", "critical": True,
                                      "manuscript": {"artifact_id": "draft", "locator": "Results"},
                                      "evidence": [{"artifact_id": "grid", "locator": "sample_minimizers"}]})
        study.passport.update(stage="experiment", next_step="Review the newly executed finite grid check.")
        study.register()
        check("new-evidence-preserves-stale-history", 2, "blocked")
        study.review("with-grid", include_experiment=True)
        study.passport.update(stage="review", next_step="Review the current manuscript and complete the fixture.")
        study.save()
        check("new-evidence-rereview-closes", 0, "eligible-for-human-review")

        # Every check invokes a fresh process; state is rebuilt only from disk.
        check("fresh-process-resume", 0, "eligible-for-human-review")
        check("wrong-research-context-rejected", 1, None, research_id="lifecycle-b")

        original_audits = copy.deepcopy(study.audits)
        study.audits = copy.deepcopy(other.audits)
        study.save()
        check("foreign-ledger-rejected", 1, None)
        study.audits = original_audits
        study.save()

        # Simulate a channel change without touching any live repository channel.
        write_json(base / "simulated-channel.json", {"commit_sha": "2" * 40})
        check("resume-keeps-original-snapshot", 0, "eligible-for-human-review")
        check("silent-snapshot-switch-blocked", 2, "blocked", sha="2" * 40)

        study.passport["pending_decisions"] = ["Author must resolve a remaining assumption."]
        study.save()
        check("pending-author-decision-blocks", 2, "blocked")
        study.passport["pending_decisions"] = []
        study.passport.update(stage="submission", next_step="Author reviews the actual evidence outside this synthetic evaluation.")
        study.save()
        check("final-records-remain-noncertifying", 0, "eligible-for-human-review")
        assert all(row["read_only"] for row in trace)

    return {"schema_version": 1, "status": "passed", "layer": "synthetic-local-cli-lifecycle",
            "workflow_sha": workflow_sha, "cases": trace, "case_count": len(trace),
            "execution": "fresh-python-process-per-check", "scientific_truth": "not-verified",
            "real_work_new_chat": "not-run", "real_work_compaction": "not-run",
            "private_repository": "not-run", "real_paper_effectiveness": "not-run"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    report = run()
    if options.output:
        write_json(options.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
