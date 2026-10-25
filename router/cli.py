"""Compile instructions and draft feedback without posting or granting permissions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import core


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    commands.add_parser("eval")
    lock = commands.add_parser("lock")
    action = lock.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    for name in ("plan", "packet"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--project", required=True)
        cmd.add_argument("--task", required=True)
        cmd.add_argument("--mode")
        cmd.add_argument("--generate-images", action="store_true", help="Declare an intended image action; does not grant permission")
        cmd.add_argument("--capability", action="append", default=[])
    cmd = commands.add_parser("receipt-check")
    cmd.add_argument("path", type=Path)
    cmd = commands.add_parser("academic-check", help="Check local research records; does not certify scientific truth")
    cmd.add_argument("passport", type=Path)
    cmd.add_argument("--research-root", type=Path, required=True)
    cmd.add_argument("--research-id", required=True)
    cmd.add_argument("--snapshot-sha", required=True)
    cmd.add_argument("--submission", action="store_true", help="Check recorded submission prerequisites for human review")
    cmd = commands.add_parser("feedback-draft")
    cmd.add_argument("--receipt", type=Path, required=True)
    cmd.add_argument("--category", required=True)
    cmd.add_argument("--observation", required=True)
    cmd.add_argument("--expected", required=True)
    cmd.add_argument("--scope", choices=["project", "shared-candidate"], default="project")
    cmd = commands.add_parser("channel")
    cmd.add_argument("name", nargs="?", default="stable")
    cmd = commands.add_parser("release-create")
    cmd.add_argument("--version", required=True)
    cmd.add_argument("--commit", required=True)
    cmd = commands.add_parser("promote")
    cmd.add_argument("--version", required=True)
    cmd.add_argument("--channel", default="stable")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "validate":
            result = core.validate(root)
        elif args.command == "eval":
            result = core.evaluate(root)
        elif args.command == "lock":
            if args.write:
                path = core.safe_path(root, core.config(root)["lockfile"])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(core.skill_lock(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            core.check_lock(root)
            result = {"status": "passed", "layer": "skill-integrity"}
        elif args.command in {"plan", "packet"}:
            result = core.plan(root, args.project, args.task, args.capability, args.mode, args.generate_images)
            if args.command == "packet":
                print(core.packet(root, result))
                return 0 if result["status"] == "ready" else 2
        elif args.command == "academic-check":
            from .academic import check_records
            result = check_records(args.passport, args.research_root, args.research_id,
                                   args.snapshot_sha, args.submission)
        elif args.command in {"receipt-check", "feedback-draft"}:
            path = args.path if args.command == "receipt-check" else args.receipt
            data = json.loads(path.read_text(encoding="utf-8"))
            if args.command == "feedback-draft":
                print(core.feedback_body(data, args.category, args.observation, args.expected, args.scope))
                return 0
            result = core.validate_receipt(data)
        elif args.command == "channel":
            result = core.read_channel(root, args.name)
        elif args.command == "release-create":
            result = core.create_release(root, args.version, args.commit)
        else:
            result = core.promote(root, args.version, args.channel)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status", "passed") in {"passed", "ready"} else 2
    except (core.RouterError, OSError, UnicodeError, json.JSONDecodeError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
