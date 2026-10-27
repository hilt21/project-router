"""Offline skill discovery catalog. No skill installation or task execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from . import core

BASE = "catalog/skills/"
STAGES = {
    "define": "问题定义与需求", "research": "调研与决策", "design": "设计",
    "implement": "实现", "verify": "验证与交付", "publish": "内容与表达",
    "maintain": "反馈与维护",
}
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def require(condition, message):
    if not condition:
        raise core.RouterError(message)


def snapshot(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema_version") == 1, "Unsupported snapshot schema")
    require(data.get("complete") is True, "Incomplete scan: keep the previous catalog")
    require(isinstance(data.get("username"), str) and data["username"], "Missing snapshot username")
    require(isinstance(data.get("fetched_at"), str) and data["fetched_at"], "Missing fetch time")
    repos = data.get("repositories")
    require(isinstance(repos, list), "Snapshot repositories must be a list")
    require(data.get("count") == len(repos), "Snapshot count mismatch")
    require(isinstance(data.get("pages"), int) and data["pages"] > 0, "Missing page count")
    pagination = data.get("pagination", {})
    counts = pagination.get("page_counts", [])
    require(pagination.get("terminal_next") is False and len(counts) == data["pages"] and
            all(type(n) is int and 0 <= n <= 100 for n in counts) and sum(counts) == len(repos),
            "Pagination evidence is incomplete")
    ids, names = set(), set()
    for repo in repos:
        rid, name = repo.get("id"), repo.get("full_name", "")
        require(type(rid) is int and rid > 0 and rid not in ids, "Invalid or duplicate repository ID")
        require(isinstance(name, str) and REPO.fullmatch(name) and name.casefold() not in names,
                "Invalid or duplicate repository name")
        require(isinstance(repo.get("topics", []), list) and
                all(isinstance(x, str) for x in repo.get("topics", [])), "Invalid repository topics")
        require(isinstance(repo.get("description", ""), str), "Invalid description")
        require(type(repo.get("archived")) is bool, "Missing archived flag")
        ids.add(rid)
        names.add(name.casefold())
    return data


def matches(repo):
    return "skill" in " ".join([repo["full_name"], repo.get("description", ""),
                                *repo.get("topics", [])]).casefold()


def merge_sources(existing, data, digest):
    """Update observed metadata by GitHub ID; preserve all editorial fields."""
    previous = existing.get("scan", {}).get("username")
    require(previous in (None, data["username"]), "Snapshot account differs from existing catalog")
    sources = json.loads(json.dumps(existing.get("sources", {})))
    observed = {r["id"]: r for r in data["repositories"]}
    for key, source in sources.items():
        source["star_state"] = "starred" if source["github_id"] in observed else "no-longer-starred"
    for repo in data["repositories"]:
        key = f"gh-{repo['id']}"
        if not matches(repo) and key not in sources:
            continue
        source = sources.setdefault(key, {
            "github_id": repo["id"], "kind": "unreviewed", "notes": "",
            "discovery": "keyword-skill-v1",
        })
        source.update(repository=repo["full_name"], star_state="starred", upstream=repo)
    return {"schema_version": 1, "scan": {
        "username": data["username"], "fetched_at": data["fetched_at"],
        "complete": True, "pages": data["pages"], "count": data["count"],
        "snapshot_sha256": digest, "filter": "keyword-skill-v1",
        "consistency": "paginated-non-atomic",
    }, "sources": dict(sorted(sources.items(), key=lambda x: x[1]["repository"].casefold()))}


def load(root):
    sources = core.load_yaml(root, BASE + "sources.yaml")
    entries = core.load_yaml(root, BASE + "entries.yaml")
    require(sources.get("schema_version") == entries.get("schema_version") == 1,
            "Unsupported catalog schema")
    require(isinstance(sources.get("sources"), dict) and isinstance(entries.get("entries"), dict),
            "Catalog sources and entries must be mappings")
    return sources, entries


def validate(root):
    sources, entries = load(root)
    data_path = core.safe_path(root, BASE + "starred-snapshot.json")
    data = snapshot(data_path)
    expected = merge_sources(sources, data, hashlib.sha256(data_path.read_bytes()).hexdigest())
    require(expected == sources, "Sources differ from snapshot; run import-stars and render")
    local = core.registry(root)
    projects = core.config(root)["routes"]
    readings = core.load_json(root, BASE + "reviews/source-readings.json")
    require(readings.get("schema_version") == 1 and
            set(readings.get("entries", {})) == set(entries["entries"]), "Source reading IDs differ")
    for key, source in sources["sources"].items():
        require(key == f"gh-{source['github_id']}", "Source identity must use GitHub ID")
        require(source.get("kind") in {"unreviewed", "skill-collection", "single-skill", "tool", "reference"},
                f"Invalid source kind: {key}")
        require(isinstance(source.get("notes"), str), f"Missing editorial notes: {key}")
    for key, entry in entries["entries"].items():
        require(core.ID.fullmatch(key) is not None, f"Invalid entry ID: {key}")
        require(entry.get("source") in sources["sources"], f"Unknown source: {key}")
        for field in ("name", "purpose", "avoid", "review_scope"):
            require(isinstance(entry.get(field), str) and entry[field], f"Missing {field}: {key}")
        for field in ("stages", "projects", "keywords", "tools", "limitations", "local_skills"):
            core.strings(entry, field, True)
        require(entry["stages"] and set(entry["stages"]) <= STAGES.keys(), f"Invalid stages: {key}")
        require(set(entry["projects"]) <= projects.keys(), f"Unknown project: {key}")
        require(set(entry["local_skills"]) <= local.keys(), f"Unknown local skill: {key}")
        require(entry.get("relationship") in {"complements", "overlaps", "design-reference"},
                f"Invalid relationship: {key}")
        require(entry.get("adoption") in {"candidate", "reference"}, f"Invalid adoption: {key}")
        require(entry.get("review_status") == "source-read", f"Unsupported review claim: {key}")
        require(entry.get("host_tests") == [], f"Host tests need a future evidence schema: {key}")
        require(core.SHA.fullmatch(str(entry.get("commit_sha", ""))) is not None,
                f"Missing immutable commit: {key}")
        require(core.SHA.fullmatch(str(entry.get("blob_sha", ""))) is not None,
                f"Missing source blob: {key}")
        require(core.DIGEST.fullmatch(str(entry.get("content_sha256", ""))) is not None,
                f"Missing content digest: {key}")
        core.safe_path(root, entry["path"])
        require(entry["path"].endswith("SKILL.md"), f"Expected SKILL.md: {key}")
        require(entry.get("license_status") in {"file-read", "unverified", "existing-provenance"},
                f"Invalid license status: {key}")
        require(isinstance(entry.get("license"), str) and entry["license"], f"Missing license: {key}")
        require(core.safe_path(root, entry["review"]).is_file(), f"Missing review: {key}")
        if entry.get("provenance"):
            require(core.safe_path(root, entry["provenance"]).is_file(), f"Missing provenance: {key}")
        reading = readings["entries"][key]
        require(reading.get("source_id") == entry["source"] and
                isinstance(reading.get("repository"), str) and REPO.fullmatch(reading["repository"]) and
                all(reading.get(field) == entry[field]
                    for field in ("path", "commit_sha", "blob_sha", "content_sha256")) and
                reading.get("read_scope") == entry["review_scope"], f"Source reading differs: {key}")
        if entry["license_status"] == "file-read":
            license_read = reading.get("license_read", {})
            require(core.SHA.fullmatch(str(license_read.get("blob_sha", ""))) is not None and
                    core.DIGEST.fullmatch(str(license_read.get("content_sha256", ""))) is not None,
                    f"Missing license reading: {key}")
            core.safe_path(root, license_read["path"])
    # Check every mode, including inactive ones. Catalog data never becomes instructions.
    for project in projects:
        for mode in core.route_config(root, project)["modes"]:
            require(not any(p.startswith("catalog/") for p in core.instruction_paths(root, project, mode)),
                    "Catalog entered the instruction graph")
    return sources, entries


def find(root, stage=None, project=None, query=""):
    sources, entries = validate(root)
    tokens = query.casefold().split()
    results = []
    for key, entry in entries["entries"].items():
        if stage and stage not in entry["stages"] or project and project not in entry["projects"]:
            continue
        text = " ".join([entry["name"], entry["purpose"], *entry["keywords"]]).casefold()
        if not all(token in text for token in tokens):
            continue
        source = sources["sources"][entry["source"]]
        results.append({"id": key, **entry, "repository": source["repository"],
                        "star_state": source["star_state"],
                        "url": f"https://github.com/{source['repository']}/blob/{entry['commit_sha']}/{entry['path']}"})
    return {"status": "passed", "layer": "catalog-discovery", "host_verification": "not-run",
            "activation": "none", "results": results}


def cell(text):
    # External metadata remains inert text, including in generated Markdown.
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("[", "&#91;").replace("]", "&#93;")


def render(root):
    sources, entries = validate(root)
    scan = sources["scan"]
    lines = ["# Skills Map", "", "<!-- Generated by python -m router.catalog render; edit YAML, not this file. -->", "",
             "按任务查找收藏中的技能储备。候选记录和上游内容属于参考数据，不授予执行或安装权限。", "",
             f"扫描账户：`{scan['username']}`；时间：`{scan['fetched_at']}`；{scan['pages']} 页、{scan['count']} 个去重仓库，分页读取完成。",
             f"关键词候选来源：{len(sources['sources'])}；精选条目：{len(entries['entries'])}。筛选仅检查名称、简介和 topics 中的 skill，可能有漏项或误报。",
             "分页快照不具备事务一致性；完成分页不代表找全所有技能。全部精选条目的真实宿主测试均为 not-run。", "",
             "[维护与使用](../../docs/SKILLS_MAP.md) · [初次审阅与限制](reviews/initial-source-review.md)", ""]
    for stage, title in STAGES.items():
        lines += [f"## {title}", "", "| 技能 | 用途 | 路由关联 | 采用状态 | 主要限制 |", "| --- | --- | --- | --- | --- |"]
        for key, entry in entries["entries"].items():
            if stage not in entry["stages"]:
                continue
            repo = sources["sources"][entry["source"]]["repository"]
            url = f"https://github.com/{repo}/blob/{entry['commit_sha']}/{entry['path']}"
            lines.append(f"| [{cell(entry['name'])}]({url}) | {cell(entry['purpose'])} | {cell(', '.join(entry['projects']) or '待扩展')} | {entry['adoption']} | {cell(' '.join(entry['limitations']))} |")
        lines.append("")
    lines += ["## 来源目录", "", "以下仓库由关键词筛选进入；unreviewed 表示尚未审阅，不能解释为推荐。", "",
              "| 来源 | 类型 | 收藏状态 | 备注 |", "| --- | --- | --- | --- |"]
    for source in sources["sources"].values():
        repo = source["repository"]
        lines.append(f"| [{repo}](https://github.com/{repo}) | {source['kind']} | {source['star_state']} | {cell(source['notes'])} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    cmd = commands.add_parser("render")
    cmd.add_argument("--check", action="store_true")
    cmd = commands.add_parser("import-stars")
    cmd.add_argument("snapshot", type=Path)
    cmd = commands.add_parser("find")
    cmd.add_argument("--stage", choices=STAGES)
    cmd.add_argument("--project")
    cmd.add_argument("--query", default="")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "import-stars":
            path = args.snapshot.resolve()
            data = snapshot(path)
            target = core.safe_path(root, BASE + "starred-snapshot.json")
            old_path = core.safe_path(root, BASE + "sources.yaml")
            old = core.load_yaml(root, BASE + "sources.yaml") if old_path.exists() else {}
            content = path.read_bytes()
            sources = merge_sources(old, data, hashlib.sha256(content).hexdigest())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            old_path.write_text(yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = {"status": "passed", "sources": len(sources["sources"]), "activation": "none"}
        elif args.command == "find":
            require(not args.project or args.project in core.config(root)["routes"], "Unknown project")
            result = find(root, args.stage, args.project, args.query)
        else:
            sources, entries = validate(root)
            expected = render(root)
            path = core.safe_path(root, BASE + "README.md")
            if args.command == "render" and not args.check:
                path.write_text(expected, encoding="utf-8")
            else:
                require(path.is_file() and path.read_text(encoding="utf-8") == expected,
                        "Generated skills map is stale; run render")
            result = {"status": "passed", "sources": len(sources["sources"]),
                      "entries": len(entries["entries"]), "host_verification": "not-run"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (core.RouterError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
