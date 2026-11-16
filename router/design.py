"""Read Design Library entries staged into the pinned content-studio snapshot."""
from __future__ import annotations

import hashlib
import unicodedata

PACKAGE = "skills/design-library"
INDEX = f"{PACKAGE}/index.json"
REPOSITORY = "hilt21/design-library"
PROJECT = "content-studio"
ADAPTER = "design-library"
STAGES = {"draft-review", "visual-plan", "image-generation"}


def alias_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def read_index(root, capabilities):
    from .core import DIGEST, ID, SHA, RouterError, load_json, safe_path, strings

    index = load_json(root, INDEX)
    commit = index.get("commit_sha")
    entries = index.get("entries")
    if (index.get("schema_version") != 1 or index.get("repository") != REPOSITORY
            or not isinstance(commit, str) or not SHA.fullmatch(commit)
            or not isinstance(entries, dict) or not entries):
        raise RouterError("Invalid Design Library index")
    aliases = {}
    for entry_id, entry in entries.items():
        if not ID.fullmatch(entry_id) or not isinstance(entry, dict) or entry.get("id") != entry_id:
            raise RouterError(f"Invalid design entry: {entry_id}")
        stages = strings(entry, "stages", True)
        if not stages or set(stages) - STAGES or PROJECT not in strings(entry, "projects", True):
            raise RouterError(f"Invalid design stage or route: {entry_id}")
        if set(strings(entry, "required_capabilities", True)) - set(capabilities):
            raise RouterError(f"Unknown design capability: {entry_id}")
        expected_file = {"skill": "SKILL.md", "instruction": "INSTRUCTIONS.md",
                         "prompt": "PROMPT.md"}.get(entry.get("type"))
        entry_path = entry.get("entry")
        prefix = f"entries/{entry_id}/"
        paths = [entry_path, *strings(entry, "dependencies", True)]
        files = entry.get("files")
        if (not expected_file or entry_path != prefix + expected_file or len(paths) != len(set(paths))
                or not isinstance(files, dict) or set(paths) != set(files)):
            raise RouterError(f"Invalid design file declaration: {entry_id}")
        for path, digest in files.items():
            name = path.removeprefix(prefix)
            if (not path.startswith(prefix) or not name.endswith(".md") or "/" in name
                    or not isinstance(digest, str) or not DIGEST.fullmatch(digest)):
                raise RouterError(f"Invalid design file: {path}")
            file = safe_path(root, f"{PACKAGE}/{path}")
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                raise RouterError(f"Design file missing or digest mismatch: {path}")
        for alias in [entry_id, *strings(entry, "aliases", True)]:
            key = alias_key(alias)
            if not key or key in aliases:
                raise RouterError(f"Conflicting design alias: {alias}")
            aliases[key] = entry_id
    return index, aliases


def select(root, project, requests, capabilities, generate_images):
    from .core import RouterError

    if project != PROJECT:
        raise RouterError(f"Design Library is unavailable for project: {project}")
    index, aliases = read_index(root, capabilities)
    matched, paths, required, stages = [], [], set(), set()
    for request in requests:
        stage, separator, query = request.partition("=")
        if not separator or stage not in STAGES or stage in stages:
            raise RouterError("Use at most one Design Library entry per stage as STAGE=ID")
        if stage == "image-generation" and not generate_images:
            raise RouterError("The image-generation stage needs --generate-images")
        entry_id = aliases.get(alias_key(query))
        entry = index["entries"].get(entry_id)
        if entry is None or stage not in entry["stages"]:
            raise RouterError(f"No design entry for {stage}: {query}")
        stages.add(stage)
        files = [f"{PACKAGE}/{path}" for path in [entry["entry"], *entry["dependencies"]]]
        paths.extend(path for path in files if path not in paths)
        required.update(entry["required_capabilities"])
        matched.append({"id": entry_id, "stage": stage, "documents": files})
    return {"repository": REPOSITORY, "commit_sha": index["commit_sha"],
            "entries": matched}, [f"{PACKAGE}/SKILL.md", INDEX, *paths], required
