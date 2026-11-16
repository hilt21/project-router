"""Resolve portable design packages using the consumer's project configuration."""
from __future__ import annotations

import hashlib
import itertools
import json
import re
import unicodedata

PACKAGE = "skills/design-library"
INDEX = f"{PACKAGE}/index.json"
BINDINGS = "registry/design-library.json"
ADAPTER = "design-library"


def alias_key(value):
    return unicodedata.normalize("NFKC", value).strip().casefold()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def files_digest(files):
    text = json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return digest(text.encode())


def bindings(root, cfg):
    from .core import ID, RouterError, load_json, strings

    data = load_json(root, BINDINGS)
    if data.get("schema_version") != 1 or not isinstance(data.get("projects"), dict):
        raise RouterError("Invalid Design Library bindings")
    for project, profile in data["projects"].items():
        if project not in cfg["routes"] or not isinstance(profile, dict) or not isinstance(profile.get("stages"), dict):
            raise RouterError(f"Unknown Design Library project: {project}")
        for stage, options in profile["stages"].items():
            if not isinstance(options, dict):
                raise RouterError(f"Invalid Design Library stage: {stage}")
            entries = strings(options, "entries", True)
            if (not ID.fullmatch(stage) or not entries or any(not ID.fullmatch(e) for e in entries)
                    or options.get("action") not in {None, "generate-images"}
                    or options.get("default", entries[0]) not in entries):
                raise RouterError(f"Invalid Design Library stage: {stage}")
        combinations = profile.get("combinations")
        if not isinstance(combinations, list):
            raise RouterError("Declare supported stage combinations")
        for group in combinations:
            if (not isinstance(group, list) or len(group) < 2 or len(group) != len(set(group))
                    or set(group) - set(profile["stages"])):
                raise RouterError("Invalid design combination")
    return data


def read_index(root, cfg):
    from .core import DIGEST, ID, SHA, RouterError, load_json, safe_path, strings

    consumer = bindings(root, cfg)
    index = load_json(root, INDEX)
    if (index.get("schema_version") not in {1, 2} or index.get("repository") != consumer["repository"]
            or not SHA.fullmatch(str(index.get("commit_sha", "")))):
        raise RouterError("Invalid Design Library index")
    entries = {}
    if index["schema_version"] == 1:
        # Support the first published import while its consumer migrates.
        for eid, old in index["entries"].items():
            prefix = f"entries/{eid}/"
            files = {path.removeprefix(prefix): value for path, value in old["files"].items()}
            entries[eid] = {**old, "entry": old["entry"].removeprefix(prefix),
                            "required": [p.removeprefix(prefix) for p in old["dependencies"]],
                            "resources": {}, "files": files, "content_sha256": files_digest(files),
                            "base": f"{PACKAGE}/entries/{eid}"}
    else:
        snapshot = index.get("snapshot")
        if (not isinstance(snapshot, str) or not re.fullmatch(r"snapshots/[0-9a-f]{40}-[0-9a-f]{12}", snapshot)
                or not snapshot.startswith(f"snapshots/{index['commit_sha']}-")):
            raise RouterError("Invalid snapshot path")
        base = f"{PACKAGE}/{snapshot}"
        expected = index.get("files")
        if not isinstance(expected, dict):
            raise RouterError("Missing snapshot file inventory")
        actual = {}
        folder = safe_path(root, base)
        for path in folder.rglob("*"):
            rel = path.relative_to(folder).as_posix()
            safe_path(root, f"{base}/{rel}")
            if path.is_file():
                actual[rel] = digest(path.read_bytes())
        if actual != expected:
            raise RouterError("Design snapshot file drift")
        for eid in strings(index, "entries", True):
            if not ID.fullmatch(eid):
                raise RouterError("Invalid design entry ID")
            entry = load_json(root, f"{base}/manifests/{eid}.json")
            entries[eid] = {**entry, "base": f"{base}/entries/{eid}"}
    aliases = {}
    for eid, entry in entries.items():
        if entry.get("id") != eid or not ID.fullmatch(eid):
            raise RouterError("Design manifest identity mismatch")
        if not strings(entry, "stages", True):
            raise RouterError("Design entry needs stages")
        if set(strings(entry, "required_capabilities", True)) - set(cfg["capabilities"]):
            raise RouterError(f"Unknown design capability: {eid}")
        paths = [entry["entry"], *strings(entry, "required", True), *entry["resources"]]
        files = entry["files"]
        if not isinstance(files, dict) or not isinstance(entry["resources"], dict):
            raise RouterError(f"Invalid design resource inventory: {eid}")
        if len(paths) != len(set(paths)) or set(paths) != set(files) or entry["content_sha256"] != files_digest(files):
            raise RouterError(f"Invalid design file declaration: {eid}")
        for path, expected in files.items():
            file = safe_path(root, f"{entry['base']}/{path}")
            if not isinstance(expected, str) or not DIGEST.fullmatch(expected) or digest(file.read_bytes()) != expected:
                raise RouterError(f"Design file digest mismatch: {eid}/{path}")
        for alias in [eid, *strings(entry, "aliases", True)]:
            key = alias_key(alias)
            if not key or key in aliases:
                raise RouterError(f"Conflicting design alias: {alias}")
            aliases[key] = eid
    for profile in consumer["projects"].values():
        for stage, options in profile["stages"].items():
            for eid in options["entries"]:
                if eid not in entries or stage not in entries[eid]["stages"]:
                    raise RouterError(f"Entry is unavailable for configured stage: {stage}/{eid}")
    return index, entries, aliases, consumer


def select(root, project, requests, cfg, generate_images, resources=None):
    from .core import RouterError

    index, entries, aliases, consumer = read_index(root, cfg)
    if project not in consumer["projects"]:
        raise RouterError(f"Design Library is unavailable for project: {project}")
    stages = consumer["projects"][project]["stages"]
    matched, paths, required, seen = [], [], set(), set()
    chosen_resources = {}
    for resource in resources or []:
        eid, separator, path = resource.partition("=")
        if not separator or eid not in entries or path not in entries[eid]["resources"]:
            raise RouterError(f"Unknown optional design resource: {resource}")
        chosen_resources.setdefault(eid, set()).add(path)
    for request in requests:
        stage, separator, query = request.partition("=")
        if stage not in stages or stage in seen:
            raise RouterError("Use one entry per configured design stage")
        options = stages[stage]
        if not separator:
            query = options.get("default", "")
        eid = aliases.get(alias_key(query))
        if eid not in options["entries"]:
            raise RouterError(f"No design entry for {stage}: {query}")
        if options.get("action") == "generate-images" and not generate_images:
            raise RouterError("The image stage needs --generate-images")
        entry = entries[eid]
        files = [entry["entry"], *entry["required"], *sorted(chosen_resources.get(eid, []))]
        documents = [{"path": f"{entry['base']}/{path}", "sha256": entry["files"][path]} for path in files]
        paths.extend(d["path"] for d in documents if d["path"] not in paths)
        required.update(entry["required_capabilities"])
        seen.add(stage)
        matched.append({"id": eid, "stage": stage, "content_sha256": entry["content_sha256"],
                        "documents": documents})
    if set(chosen_resources) - {m["id"] for m in matched}:
        raise RouterError("Optional resources must belong to a selected design entry")
    if len(seen) > 1 and not any(seen == set(group) for group in consumer["projects"][project]["combinations"]):
        raise RouterError("Design stage combination is not configured")
    selection = {"schema_version": 2, "repository": index["repository"],
                 "commit_sha": index["commit_sha"], "entries": matched}
    return selection, [f"{PACKAGE}/SKILL.md", *paths], required


def validation_requests(root, cfg):
    _, _, _, consumer = read_index(root, cfg)
    for project, profile in consumer["projects"].items():
        stages = profile["stages"]
        groups = [[stage] for stage in stages] + profile["combinations"]
        for group in groups:
            for ids in itertools.product(*(stages[stage]["entries"] for stage in group)):
                requests = [f"{stage}={eid}" for stage, eid in zip(group, ids)]
                generate = any(stages[stage].get("action") == "generate-images" for stage in group)
                yield project, requests, generate


def validate_receipt(data, root, artifact_root=None):
    from .core import DIGEST, SHA, RouterError, config, git_identity, route_config, safe_path

    selection = data.get("design_library")
    if selection is None:
        return
    if (not isinstance(selection, dict) or selection.get("schema_version") != 2
            or not SHA.fullmatch(str(selection.get("commit_sha", "")))
            or not isinstance(selection.get("entries"), list) or not selection["entries"]):
        raise RouterError("Invalid design receipt provenance")
    if root is None:
        raise RouterError("Design receipts need the corresponding router snapshot root")
    cfg = config(root)
    if data["mode"] not in route_config(root, data["project_id"])["modes"]:
        raise RouterError("Design receipt has an unsupported mode")
    requests, resources = [], []
    _, entries, _, _ = read_index(root, cfg)
    for record in selection["entries"]:
        if not isinstance(record, dict) or not isinstance(record.get("documents"), list):
            raise RouterError("Invalid design receipt entry")
        eid, stage = record.get("id"), record.get("stage")
        if not isinstance(eid, str) or not isinstance(stage, str) or eid not in entries:
            raise RouterError("Unknown design receipt entry")
        requests.append(f"{stage}={eid}")
        for document in record.get("documents", []):
            prefix = entries[eid]["base"] + "/"
            if not isinstance(document, dict) or not str(document.get("path", "")).startswith(prefix):
                raise RouterError("Invalid design receipt document")
            path = document["path"][len(prefix):]
            if path in entries[eid]["resources"]:
                resources.append(f"{eid}={path}")
    expected, _, _ = select(root, data["project_id"], requests, cfg, True, resources)
    if expected != selection or data["snapshot_sha"] != git_identity(root)["sha"]:
        raise RouterError("Design receipt does not match the pinned router snapshot")
    readback = {item["path"]: item["sha256"] for item in data["source_readback"]}
    for record in selection["entries"]:
        for document in record["documents"]:
            if ((data["status"] == "complete" or document["path"] in readback)
                    and readback.get(document["path"]) != document["sha256"]):
                raise RouterError("Design receipt is missing a matching source readback")
    artifacts = data.get("artifacts", [])
    if not isinstance(artifacts, list) or (data["status"] == "complete" and not artifacts):
        raise RouterError("Complete design receipt needs artifact evidence")
    for artifact in artifacts:
        if (not isinstance(artifact, dict) or not DIGEST.fullmatch(str(artifact.get("sha256", "")))
                or artifact_root is None):
            raise RouterError("Artifact evidence needs hashes and --artifact-root")
        file = safe_path(artifact_root, artifact.get("path"))
        if not file.is_file() or digest(file.read_bytes()) != artifact["sha256"]:
            raise RouterError("Design artifact digest mismatch")
