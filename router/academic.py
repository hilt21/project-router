"""Read-only consistency checks for research records; never establish scientific truth."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .core import DIGEST, ID, SHA, RouterError, safe_path

STAGES = {"scope", "literature", "math", "experiment", "write", "review", "submission"}
CHECKS = {"coverage", "reference-existence", "claim-support", "mathematical-rigor",
          "experiment-validity", "novelty-scope", "originality", "journal-compliance", "review-resolution"}
GLOBAL_CHECKS = {"coverage", "originality", "journal-compliance", "review-resolution"}
CLAIM_CHECKS = {
    "external-fact": {"reference-existence", "claim-support"},
    "mathematical": {"mathematical-rigor"},
    "experimental": {"experiment-validity"},
    "novelty": {"novelty-scope"},
    "interpretation": {"claim-support"},
}
STATUSES = {"passed", "failed", "unknown", "not-run", "not-applicable"}


def require(condition, message):
    if not condition:
        raise RouterError(message)


def mapping(value, name):
    require(isinstance(value, dict), f"{name} must be an object")
    return value


def rows(value, name):
    require(isinstance(value, list), f"{name} must be an array")
    return value


def nonempty(value, name):
    require(isinstance(value, str) and bool(value.strip()), f"Missing {name}")
    return value


def identifiers(value, name):
    result = rows(value, name)
    require(all(isinstance(x, str) and ID.fullmatch(x) for x in result), f"Invalid {name}")
    require(len(result) == len(set(result)), f"Duplicate {name}")
    return result


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RouterError(f"Cannot read research record: {path.name}") from exc
    return mapping(value, path.name)


def record_header(record, research_id, label):
    require(record.get("schema_version") == 1, f"Unsupported {label} schema")
    require(record.get("research_id") == research_id, f"Research ID mismatch: {label}")


def binding_map(value, name):
    value = mapping(value, name)
    require(all(isinstance(k, str) and ID.fullmatch(k) and isinstance(v, str) and DIGEST.fullmatch(v)
                for k, v in value.items()), f"Invalid {name}")
    return value


def check_records(passport_path: Path, research_root: Path, research_id: str,
                  snapshot_sha: str, submission=False) -> dict:
    """Validate explicit local files and surface stale checks without editing any record."""
    require(isinstance(research_id, str) and ID.fullmatch(research_id), "Invalid research ID")
    require(isinstance(snapshot_sha, str) and SHA.fullmatch(snapshot_sha), "Full workflow SHA required")
    root = research_root.absolute()
    passport_path = passport_path.absolute()
    require(passport_path.is_relative_to(root), "Passport escapes research root")
    passport = read_object(safe_path(root, passport_path.relative_to(root).as_posix()))
    record_header(passport, research_id, "passport")
    require(passport.get("project_id") == "academic-research", "Academic project ID required")
    require(isinstance(passport.get("workflow_sha"), str) and SHA.fullmatch(passport["workflow_sha"]),
            "Invalid passport workflow SHA")
    require(passport.get("stage") in STAGES, "Invalid academic stage")
    require(passport.get("stage_status") in {"planned", "partial", "complete", "blocked", "unknown"},
            "Invalid academic stage status")
    rows(passport.get("pending_decisions"), "pending_decisions")
    nonempty(passport.get("next_step"), "next_step")
    issues = []
    if passport["workflow_sha"] != snapshot_sha:
        issues.append("workflow-snapshot-mismatch")

    artifacts = {}
    for entry in rows(passport.get("artifacts"), "artifacts"):
        entry = mapping(entry, "artifact")
        artifact_id = entry.get("id")
        require(isinstance(artifact_id, str) and ID.fullmatch(artifact_id), "Invalid artifact ID")
        require(artifact_id not in artifacts, "Duplicate artifact ID")
        require(isinstance(entry.get("sha256"), str) and DIGEST.fullmatch(entry["sha256"]), "Invalid artifact digest")
        path = safe_path(root, entry.get("path"))
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            actual = None
        artifacts[artifact_id] = {**entry, "actual_sha256": actual, "current": actual == entry["sha256"]}
        if actual != entry["sha256"]:
            issues.append(f"artifact-stale-or-missing:{artifact_id}")

    claims_id = passport.get("claim_ledger")
    require(isinstance(claims_id, str) and claims_id in artifacts, "Unknown claim ledger artifact")
    claim_ledger = read_object(safe_path(root, artifacts[claims_id]["path"]))
    record_header(claim_ledger, research_id, "claim ledger")
    coverage = mapping(claim_ledger.get("coverage"), "claim coverage")
    require(coverage.get("semantic_extraction") in {"unknown", "human-attested"}, "Invalid semantic coverage label")
    candidates = rows(coverage.get("unregistered_candidates"), "unregistered_candidates")
    require(all(isinstance(x, str) and x.strip() for x in candidates), "Invalid unregistered candidate")

    def evidence_refs(value, label):
        refs = rows(value, label)
        for ref in refs:
            ref = mapping(ref, label)
            require(isinstance(ref.get("artifact_id"), str) and ref["artifact_id"] in artifacts,
                    f"Unknown evidence artifact: {label}")
            nonempty(ref.get("locator"), f"{label} locator")
        return refs

    claims = {}
    for claim in rows(claim_ledger.get("claims"), "claims"):
        claim = mapping(claim, "claim")
        claim_id = claim.get("id")
        require(isinstance(claim_id, str) and ID.fullmatch(claim_id) and claim_id not in claims, "Invalid or duplicate claim ID")
        require(claim.get("kind") in CLAIM_CHECKS, "Invalid claim kind")
        require(isinstance(claim.get("critical"), bool), "Claim critical must be boolean")
        nonempty(claim.get("text"), "claim text")
        evidence_refs([claim.get("manuscript")], "claim manuscript")
        evidence_refs(claim.get("evidence"), "claim evidence")
        claims[claim_id] = claim

    audit_pointer = mapping(passport.get("audit_ledger"), "audit_ledger")
    require(isinstance(audit_pointer.get("sha256"), str) and DIGEST.fullmatch(audit_pointer["sha256"]),
            "Invalid audit ledger digest")
    audit_path = safe_path(root, audit_pointer.get("path"))
    audit_ledger = read_object(audit_path)
    record_header(audit_ledger, research_id, "audit ledger")
    audit_current = hashlib.sha256(audit_path.read_bytes()).hexdigest() == audit_pointer["sha256"]
    if not audit_current:
        issues.append("audit-ledger-stale")
    audits, superseded = {}, set()
    for audit in rows(audit_ledger.get("audits"), "audits"):
        audit = mapping(audit, "audit")
        audit_id = audit.get("id")
        require(isinstance(audit_id, str) and ID.fullmatch(audit_id) and audit_id not in audits, "Invalid or duplicate audit ID")
        require(audit.get("check") in CHECKS, "Unknown academic check")
        require(audit.get("status") in STATUSES, "Invalid audit status")
        require(audit.get("kind") in {"tool-readback", "artifact-check", "human-check", "self-report"}, "Invalid evidence kind")
        targets = identifiers(audit.get("claim_ids"), "audit claim_ids")
        require(set(targets) <= set(claims), "Audit references an unknown claim")
        evidence = evidence_refs(audit.get("evidence"), "audit evidence")
        nonempty(audit.get("reason"), "audit reason")
        findings = rows(audit.get("blocking_findings"), "blocking_findings")
        limitations = rows(audit.get("limitations"), "limitations")
        require(all(isinstance(x, str) and x.strip() for x in findings + limitations), "Invalid audit finding")
        bindings = binding_map(audit.get("input_bindings"), "audit input_bindings")
        require(set(bindings) <= set(artifacts), "Audit binds an unknown artifact")
        previous = identifiers(audit.get("supersedes", []), "supersedes")
        for old in previous:
            require(old in audits and old not in superseded, "Superseded audit must be an active earlier record")
            require(audits[old]["check"] == audit["check"] and set(audits[old]["claim_ids"]) == set(targets),
                    "Superseding audit must preserve check and claim scope")
            superseded.add(old)
        if audit["status"] in {"passed", "not-applicable"}:
            required_inputs = {claims_id}
            if audit["status"] == "passed":
                bound_claims = list(claims.values()) if audit["check"] in GLOBAL_CHECKS else [claims[x] for x in targets]
                for claim in bound_claims:
                    required_inputs.add(claim["manuscript"]["artifact_id"])
                    required_inputs.update(ref["artifact_id"] for ref in claim["evidence"])
                required_inputs.update(ref["artifact_id"] for ref in evidence)
            require(required_inputs <= set(bindings), "Audit omits required input bindings")
        if audit["status"] == "passed":
            require(audit["kind"] != "self-report" and bool(evidence), "Passing audit requires observable evidence")
            require(not findings, "Passing audit cannot retain blocking findings")
        current = audit_current and all(artifacts[x]["current"] and artifacts[x]["sha256"] == digest
                                        for x, digest in bindings.items())
        audits[audit_id] = {**audit, "current": current}

    active = [audit for key, audit in audits.items() if key not in superseded]
    for audit in active:
        if not audit["current"]:
            issues.append(f"audit-stale:{audit['id']}")
    blockers = list(issues)
    if submission:
        if not claims:
            blockers.append("empty-claim-registry")
        if candidates:
            blockers.append("unregistered-claim-candidates")
        if passport["pending_decisions"]:
            blockers.append("pending-research-decisions")
        for audit in active:
            if audit["blocking_findings"] or audit["status"] == "failed":
                blockers.append(f"unresolved-audit:{audit['id']}")
        for check in sorted(CHECKS):
            applicable = list(claims) if check in GLOBAL_CHECKS else [key for key, claim in claims.items()
                                                                     if check in CLAIM_CHECKS[claim["kind"]]]
            candidates_for_check = [a for a in active if a["check"] == check and a["current"]]
            if not applicable and check not in GLOBAL_CHECKS:
                if not any(a["status"] == "not-applicable" for a in candidates_for_check):
                    blockers.append(f"missing-not-applicable-record:{check}")
                continue
            for claim_id in applicable:
                if not claims[claim_id]["evidence"]:
                    blockers.append(f"claim-without-evidence:{claim_id}")
                if not any(a["status"] == "passed" and (check in GLOBAL_CHECKS or claim_id in a["claim_ids"])
                           for a in candidates_for_check):
                    blockers.append(f"missing-current-pass:{check}:{claim_id}")
    blockers = list(dict.fromkeys(blockers))
    return {
        "status": "blocked" if blockers else "passed", "layer": "academic-record-consistency",
        "research_id": research_id, "workflow_sha": passport["workflow_sha"],
        "stage": passport["stage"], "stage_status": passport["stage_status"],
        "submission_status": ("blocked" if blockers else "eligible-for-human-review") if submission else "not-checked",
        "registered_claims": len(claims), "critical_claims": sum(c["critical"] for c in claims.values()),
        "semantic_extraction": coverage["semantic_extraction"], "scientific_truth": "not-verified",
        "blockers": blockers,
        "artifacts": [{"id": x["id"], "current": x["current"]} for x in artifacts.values()],
        "audits": [{"id": a["id"], "check": a["check"], "status": a["status"],
                    "validity": "current" if a["current"] else "stale", "superseded": key in superseded}
                   for key, a in audits.items()],
        "mutations_authorized": False,
    }
