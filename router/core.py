"""Validate and compile versioned instructions. Never execute business tools."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

import yaml

SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"v\d+\.\d+\.\d+(?:-[a-z0-9.]+)?\Z")
SECRET = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{16,})", re.I)


class RouterError(ValueError):
    """Invalid or incomplete configuration; do not silently fall back."""


class UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            if key in result:
                raise RouterError(f"Duplicate YAML key: {key}")
        except TypeError as exc:
            raise RouterError("YAML keys must be scalar") from exc
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def safe_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise RouterError(f"Invalid repository path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in {"..", ".git"} for p in path.parts):
        raise RouterError(f"Disallowed repository path: {name}")
    target = root / name
    if not target.resolve().is_relative_to(root.resolve()):
        raise RouterError(f"Path escapes repository: {name}")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise RouterError(f"Symlink in instruction path: {name}")
    return target


def read_text(root: Path, path: str) -> str:
    file = safe_path(root, path)
    if not file.is_file():
        raise RouterError(f"Missing file: {path}")
    return file.read_text(encoding="utf-8")


def parse_yaml(text: str, name: str) -> dict:
    try:
        data = yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise RouterError(f"Invalid YAML in {name}: {exc}") from exc
    if not isinstance(data, dict):
        raise RouterError(f"Expected mapping in {name}")
    return data


def load_yaml(root: Path, path: str) -> dict:
    return parse_yaml(read_text(root, path), path)


def load_json(root: Path, path: str) -> dict:
    try:
        data = json.loads(read_text(root, path))
    except json.JSONDecodeError as exc:
        raise RouterError(f"Invalid JSON in {path}") from exc
    if not isinstance(data, dict):
        raise RouterError(f"Expected object in {path}")
    return data


def document(root: Path, path: str) -> tuple[dict, str]:
    text = read_text(root, path)
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise RouterError(f"Missing frontmatter: {path}")
    return parse_yaml(match[1], path), match[2]


def strings(data: dict, key: str, required=False) -> list[str]:
    value = data.get(key, None if required else [])
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise RouterError(f"{key} must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise RouterError(f"Duplicate entries in {key}")
    return value


def config(root: Path) -> dict:
    data = load_yaml(root, "project-router.yaml")
    if data.get("schema_version") != 1:
        raise RouterError("Unsupported config schema")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", data.get("repository", "")):
        raise RouterError("Invalid repository")
    if not isinstance(data.get("routes"), dict) or not data["routes"]:
        raise RouterError("routes must be a nonempty mapping")
    if not isinstance(data.get("max_packet_bytes"), int) or data["max_packet_bytes"] <= 0:
        raise RouterError("max_packet_bytes must be positive")
    if not ID.fullmatch(data.get("default_channel", "")):
        raise RouterError("Invalid default_channel")
    strings(data, "capabilities", True)
    for project, path in data["routes"].items():
        if not isinstance(project, str) or not ID.fullmatch(project):
            raise RouterError("Invalid project ID")
        safe_path(root, path)
    return data


def registry(root: Path, cfg=None) -> dict:
    cfg = cfg or config(root)
    data = load_yaml(root, cfg["registry"])
    if data.get("schema_version") != 1 or not isinstance(data.get("skills"), dict):
        raise RouterError("Invalid skill registry")
    for name, entry in data["skills"].items():
        if not isinstance(name, str) or not ID.fullmatch(name) or len(name) > 64:
            raise RouterError(f"Invalid skill ID: {name}")
        if not isinstance(entry, dict) or entry.get("source") != "local" or entry.get("activation") != "document":
            raise RouterError(f"Unsupported skill source or activation: {name}")
        if entry.get("path") != f"skills/{name}/SKILL.md" or not entry.get("license"):
            raise RouterError(f"Invalid skill path or license: {name}")
        if set(strings(entry, "required_capabilities")) - set(cfg["capabilities"]):
            raise RouterError(f"Unknown skill capability: {name}")
        meta, body = document(root, entry["path"])
        desc = meta.get("description")
        if meta.get("name") != name or not isinstance(desc, str) or not 1 <= len(desc) <= 1024 or not body.strip():
            raise RouterError(f"Invalid skill metadata: {name}")
        if len(body.splitlines()) > 500:
            raise RouterError(f"Skill exceeds 500 lines: {name}")
    return data["skills"]


def skill_lock(root: Path) -> dict:
    entries = {}
    for name, entry in sorted(registry(root).items()):
        folder = safe_path(root, entry["path"]).parent
        files = {}
        for file in sorted(folder.rglob("*")):
            relative = file.relative_to(root).as_posix()
            safe_path(root, relative)
            if file.is_file():
                files[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
        entries[name] = {"path": entry["path"], "activation": entry["activation"], "files": files}
    return {"schema_version": 1, "skills": entries}


def check_lock(root: Path) -> None:
    if load_json(root, config(root)["lockfile"]) != skill_lock(root):
        raise RouterError("Skill lock mismatch; review changes before running lock --write")


def route_config(root: Path, project: str) -> dict:
    cfg = config(root)
    if project not in cfg["routes"]:
        raise RouterError(f"Unknown project ID: {project}")
    route, _ = document(root, cfg["routes"][project])
    if route.get("id") != project or route.get("schema_version") not in {1, 2}:
        raise RouterError("Route ID or schema mismatch")
    modes = strings(route, "modes", True)
    if not modes or any(not ID.fullmatch(mode) for mode in modes):
        raise RouterError("Route needs valid modes")
    strings(route, "skills", True)
    if route["schema_version"] == 1:
        if any(key in route for key in ("mode_config", "default_mode", "needs_input_modes")):
            raise RouterError("Mode configuration requires route schema 2")
        return route
    if route.get("default_mode") not in modes:
        raise RouterError("default_mode must name a declared mode")
    if set(strings(route, "needs_input_modes")) - set(modes):
        raise RouterError("Unknown needs_input mode")
    profiles = route.get("mode_config")
    if not isinstance(profiles, dict) or set(profiles) != set(modes):
        raise RouterError("mode_config must cover exactly the declared modes")
    allowed = {"includes", "rules", "skills", "required_capabilities", "optional_capabilities"}
    for mode, profile in profiles.items():
        if not isinstance(profile, dict) or set(profile) - allowed:
            raise RouterError(f"Invalid mode configuration: {mode}")
        for key in allowed:
            strings(profile, key)
    return route


def resolve_mode(route: dict, task: str, explicit=None) -> str:
    if route["schema_version"] == 1:
        return select_mode(route["modes"], task, explicit)
    chosen = explicit if explicit is not None else route["default_mode"]
    if chosen not in route["modes"]:
        raise RouterError(f"Unsupported mode: {chosen}")
    return chosen


def instruction_graph(root: Path, project: str, mode=None) -> dict:
    cfg = config(root)
    skills = registry(root, cfg)
    route = route_config(root, project)
    chosen = resolve_mode(route, "", mode)
    if chosen not in route["modes"]:
        raise RouterError("Route does not support resolved mode")
    profile = route.get("mode_config", {}).get(chosen, {})
    result, active, selected = [], [], []
    required, optional = set(), set()

    def visit(path):
        if path in active:
            raise RouterError("Instruction cycle: " + " -> ".join([*active, path]))
        if path in result:
            return
        active.append(path)
        meta, _ = document(root, path)
        if meta.get("project_id", project) != project:
            raise RouterError(f"Cross-project workflow: {path}")
        if "project_ids" in meta and project not in strings(meta, "project_ids", True):
            raise RouterError(f"Cross-project rule: {path}")
        refs = strings(meta, "includes") + strings(meta, "rules")
        if "workflow" in meta:
            refs.append(meta["workflow"])
        names = strings(meta, "skills")
        if path == cfg["routes"][project]:
            refs += strings(profile, "includes") + strings(profile, "rules")
            names += strings(profile, "skills")
            required.update(strings(profile, "required_capabilities"))
            optional.update(strings(profile, "optional_capabilities"))
        required.update(strings(meta, "required_capabilities"))
        optional.update(strings(meta, "optional_capabilities"))
        for name in names:
            if name not in skills:
                raise RouterError(f"Unknown skill: {name}")
            if name not in selected:
                selected.append(name)
            required.update(strings(skills[name], "required_capabilities"))
            refs.append(skills[name]["path"])
        result.append(path)
        for ref in refs:
            visit(ref)
        active.pop()

    visit(cfg["routes"][project])
    if (required | optional) - set(cfg["capabilities"]):
        raise RouterError("Unknown instruction capability")
    total = sum(len(read_text(root, p).encode()) for p in result)
    if total > cfg["max_packet_bytes"]:
        raise RouterError(f"Instruction packet exceeds byte budget: {total}")
    return {"paths": result, "skills": selected, "required_capabilities": required,
            "optional_capabilities": optional - required}


def instruction_paths(root: Path, project: str, mode=None) -> list[str]:
    return instruction_graph(root, project, mode)["paths"]


def select_mode(modes: list[str], task: str, explicit=None) -> str:
    if explicit:
        if explicit not in modes:
            raise RouterError(f"Unsupported mode: {explicit}")
        return explicit
    if modes == ["research"]:
        return "research"
    # Conservative helper. A host can resolve context, then supply --mode.
    wechat = bool(re.search(r"wechat|weixin|微信|公众号", task, re.I))
    linkedin = bool(re.search(r"linkedin", task, re.I))
    return "wechat" if wechat and not linkedin else "linkedin" if linkedin and not wechat else "select-channel"


def git_identity(root: Path) -> dict:
    try:
        sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip())
        return {"kind": "working-tree" if dirty else "git-commit", "sha": None if dirty else sha, "base_sha": sha}
    except subprocess.CalledProcessError:
        return {"kind": "working-tree", "sha": None, "base_sha": None}


def plan(root: Path, project: str, task: str, capabilities: list[str], mode=None, generate_images=False) -> dict:
    cfg = config(root)
    check_lock(root)
    if set(capabilities) - set(cfg["capabilities"]):
        raise RouterError("Unknown capabilities: " + ", ".join(sorted(set(capabilities) - set(cfg["capabilities"]))))
    route = route_config(root, project)
    chosen = resolve_mode(route, task, mode)
    if chosen not in route["modes"]:
        raise RouterError("Route does not support resolved mode")
    graph = instruction_graph(root, project, chosen)
    paths, selected = graph["paths"], graph["skills"]
    required, optional = graph["required_capabilities"], graph["optional_capabilities"]
    # A mention of images may be a negation or a request for a brief. The host
    # resolves the requested stage and passes the intended action explicitly.
    if generate_images:
        required.add("image-generation")
    missing = sorted(required - set(capabilities))
    input_modes = route.get("needs_input_modes", ["select-channel"])
    return {
        "schema_version": 1, "project_id": project, "mode": chosen,
        "status": "blocked" if missing else "needs-input" if chosen in input_modes else "ready",
        "source": git_identity(root), "required_capabilities": sorted(required), "missing_capabilities": missing,
        "optional_capabilities": sorted(optional), "missing_optional_capabilities": sorted(optional - set(capabilities)),
        "intended_actions": ["generate-images"] if generate_images else [],
        "skills": [{"id": name, "activation": "document"} for name in selected],
        "documents": [{"path": p, "sha256": hashlib.sha256(read_text(root, p).encode()).hexdigest()} for p in paths],
        "mutations_authorized": False,
        "authorization_note": "A packet never grants permission; use actual user authorization and host policy.",
        "behavioral_verification": "not-run",
    }


def packet(root: Path, result: dict) -> str:
    text = "# Execution packet\n\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for item in result["documents"]:
        text += f"\n## Source: {item['path']}\n\nSHA-256: {item['sha256']}\n\n" + read_text(root, item["path"])
    if len(text.encode("utf-8")) > config(root)["max_packet_bytes"]:
        raise RouterError(f"Execution packet exceeds byte budget: {len(text.encode('utf-8'))}")
    return text


def validate(root: Path) -> dict:
    cfg = config(root)
    check_lock(root)
    projects = []
    for project, path in cfg["routes"].items():
        meta = route_config(root, project)
        modes = []
        for mode in meta["modes"]:
            result = plan(root, project, "", cfg["capabilities"], mode)
            modes.append({"mode": mode, "documents": len(result["documents"]),
                          "packet_bytes": len(packet(root, result).encode("utf-8"))})
        projects.append({"id": project, "modes": modes})
    for file in root.rglob("*.md"):
        if any(p.startswith(".") or p in {"build", "__pycache__"} for p in file.relative_to(root).parts):
            continue
        text = re.sub(r"```.*?```", "", file.read_text(encoding="utf-8"), flags=re.S)
        for link in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            link = link.strip("<>")
            if urlparse(link).scheme or link.startswith("#"):
                continue
            target = unquote(link.split("#", 1)[0])
            candidate = file.parent / target
            if not candidate.resolve().is_relative_to(root.resolve()):
                raise RouterError(f"Markdown link escapes repository: {file.relative_to(root)}")
            # Relative parent links are legitimate in human docs, unlike instruction refs.
            relative = candidate.resolve().relative_to(root.resolve()).as_posix()
            if not safe_path(root, relative).exists():
                raise RouterError(f"Broken Markdown link in {file.relative_to(root)}: {link}")
    channels = []
    for channel in sorted((root / "channels").glob("*.json")):
        entry = read_channel(root, channel.stem)
        channels.append({"channel": channel.stem, "version": entry["version"], "sha": entry["commit_sha"]})
    return {"status": "passed", "layer": "static", "projects": projects, "skills": len(registry(root)), "channels": channels, "behavioral_verification": "not-run"}


def read_channel(root: Path, name: str) -> dict:
    if not ID.fullmatch(name):
        raise RouterError("Invalid channel")
    data = load_json(root, f"channels/{name}.json")
    if data.get("schema_version") != 1 or data.get("repository") != config(root)["repository"]:
        raise RouterError("Channel schema or repository mismatch")
    if not SHA.fullmatch(str(data.get("commit_sha", ""))) or not VERSION.fullmatch(str(data.get("version", ""))):
        raise RouterError("Channel needs an immutable SHA and version")
    if data != load_json(root, f"releases/{data['version']}.json"):
        raise RouterError("Channel differs from immutable release record")
    validate_route_map(root, data.get("routes"))
    return data


def validate_route_map(root: Path, routes) -> None:
    # The released route map belongs to its source version, not today's main.
    if not isinstance(routes, dict) or not routes:
        raise RouterError("Invalid released route map")
    for project, path in routes.items():
        if not isinstance(project, str) or not ID.fullmatch(project):
            raise RouterError("Invalid released project ID")
        safe_path(root, path)


def create_release(root: Path, version: str, commit: str) -> dict:
    if not VERSION.fullmatch(version) or not SHA.fullmatch(commit):
        raise RouterError("Use a semantic version and full lowercase commit SHA")
    try:
        resolved = subprocess.check_output(["git", "-C", str(root), "rev-parse", f"{commit}^{{commit}}"], stderr=subprocess.DEVNULL, text=True).strip()
    except subprocess.CalledProcessError as exc:
        raise RouterError("Release source commit unavailable locally") from exc
    if resolved != commit:
        raise RouterError("Release source commit mismatch")
    governed = ["project-router.yaml", "pyproject.toml", "AGENTS.md", ".github", "bootstrap", "router", "routes", "rules", "workflows", "skills", "registry", "tests", "evals", "BOOTSTRAP.md", "docs/PROTOCOL.md", "templates", "feedback", "scripts"]
    diff = subprocess.check_output(["git", "-C", str(root), "diff", commit, "--", *governed], text=True)
    untracked = subprocess.check_output(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "--", *governed], text=True)
    if diff or untracked:
        raise RouterError("Governed files differ from release commit")
    validate(root)
    path = safe_path(root, f"releases/{version}.json")
    if path.exists():
        raise RouterError("Release already exists; versions are immutable")
    data = {"schema_version": 1, "repository": config(root)["repository"], "version": version, "commit_sha": commit,
            "routes": config(root)["routes"], "created_at": datetime.now(timezone.utc).isoformat(), "maturity": "preview",
            "verification": {"static": "passed", "work_fresh_chat": "not-run", "work_compaction": "not-run", "private_repository": "not-run"}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def promote(root: Path, version: str, channel: str) -> dict:
    if not VERSION.fullmatch(version) or not ID.fullmatch(channel):
        raise RouterError("Invalid release or channel")
    data = load_json(root, f"releases/{version}.json")
    if data.get("repository") != config(root)["repository"] or not SHA.fullmatch(str(data.get("commit_sha", ""))):
        raise RouterError("Invalid release record")
    if data.get("version") != version or data.get("schema_version") != 1:
        raise RouterError("Release metadata mismatch")
    validate_route_map(root, data.get("routes"))
    path = safe_path(root, f"channels/{channel}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return read_channel(root, channel)


def validate_receipt(data: dict) -> dict:
    if data.get("schema_version") != 1:
        raise RouterError("Invalid receipt schema")
    for key in ("run_id", "project_id", "mode", "status", "created_at"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise RouterError(f"Missing receipt {key}")
    if not ID.fullmatch(data["project_id"]):
        raise RouterError("Invalid receipt project_id")
    status = data["status"]
    if status not in {"complete", "partial", "blocked", "failed", "unknown"}:
        raise RouterError("Invalid receipt status")
    try:
        when = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise RouterError("Invalid receipt time") from exc
    if when.tzinfo is None:
        raise RouterError("Receipt time must include timezone")
    sha = data.get("snapshot_sha")
    if not (isinstance(sha, str) and SHA.fullmatch(sha)) and not (sha is None and status == "unknown"):
        raise RouterError("Full SHA required; unknown source requires unknown status")
    for key in ("source_readback", "skills", "verification", "unverified"):
        if not isinstance(data.get(key), list):
            raise RouterError(f"Receipt {key} must be a list")
    for entry in data["source_readback"]:
        if not isinstance(entry, dict) or not entry.get("path") or not DIGEST.fullmatch(str(entry.get("sha256", ""))) or not entry.get("tool"):
            raise RouterError("Invalid source readback entry")
    for entry in data["skills"]:
        if not isinstance(entry, dict) or not ID.fullmatch(str(entry.get("id", ""))) or entry.get("activation") not in {"document", "native", "unavailable"}:
            raise RouterError("Invalid receipt skill")
    for check in data["verification"]:
        if not isinstance(check, dict) or not check.get("check") or check.get("status") not in {"passed", "failed", "not-run", "unknown"}:
            raise RouterError("Invalid verification entry")
        if check.get("kind") not in {"tool-readback", "artifact-check", "human-check", "self-report"}:
            raise RouterError("Invalid evidence kind")
        evidence = check.get("evidence", [])
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x for x in evidence):
            raise RouterError("Invalid evidence references")
        if check["status"] == "passed" and (not evidence or check["kind"] == "self-report"):
            raise RouterError("Passing checks need observable evidence beyond self-report")
    if status == "complete" and (not data["source_readback"] or not data["verification"] or any(c["status"] != "passed" for c in data["verification"])):
        raise RouterError("Complete receipt needs source readback and passing checks")
    if SECRET.search(json.dumps(data)):
        raise RouterError("Potential credential in receipt; redact before sharing")
    return {"status": "passed", "layer": "receipt-structure", "authenticity": "not-verified"}


def feedback_body(receipt: dict, category: str, observation: str, expected: str, scope: str) -> str:
    validate_receipt(receipt)
    if category not in {"routing", "quality", "environment", "conflict", "preference", "unknown"}:
        raise RouterError("Invalid feedback category")
    if scope not in {"project", "shared-candidate"}:
        raise RouterError("Invalid feedback scope")
    if not observation.strip() or not expected.strip():
        raise RouterError("Observation and expected behavior are required")
    if SECRET.search(observation + expected):
        raise RouterError("Potential credential in feedback")
    return (f"## Context\n\nProject: `{receipt['project_id']}`\n\nSource SHA: `{receipt.get('snapshot_sha') or 'unknown'}`\n\n"
            f"Run: `{receipt['run_id']}`\n\nCategory: `{category}`\n\nScope: `{scope}`\n\n"
            f"## Observed\n\n{observation.strip()}\n\n## Expected\n\n{expected.strip()}\n\n## Evidence\n\n" +
            "\n".join(f"- {e}" for c in receipt["verification"] for e in c.get("evidence", [])) +
            "\n\n## Change proposal\n\nReproduce first. Add a counterexample and compare the candidate with the current release. No automatic global promotion.\n")


def evaluate(root: Path) -> dict:
    suite = load_yaml(root, "evals/routing.yaml")
    if suite.get("schema_version") != 1 or not isinstance(suite.get("cases"), list):
        raise RouterError("Invalid routing suite")
    results = []
    for case in suite["cases"]:
        try:
            result = plan(root, case["project_id"], case["task"], case["capabilities"], case.get("mode"), case.get("generate_images", False))
            failures = [f"{k}: expected {v!r}, got {result.get(k)!r}" for k, v in case["expected"].items() if result.get(k) != v]
        except RouterError as exc:
            failures = [] if case.get("expected_error") and case["expected_error"] in str(exc) else [str(exc)]
        else:
            if "expected_error" in case:
                failures.append("Expected an error")
        results.append({"id": case["id"], "status": "failed" if failures else "passed", "failures": failures})
    return {"status": "passed" if all(x["status"] == "passed" for x in results) else "failed", "layer": "deterministic-routing", "cases": results, "behavioral_verification": "not-run"}
