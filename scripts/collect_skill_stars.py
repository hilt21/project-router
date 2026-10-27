"""Collect public GitHub stars as data; never install or activate skills."""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path


def collect(username, fetch=urllib.request.urlopen):
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", username):
        raise ValueError("Invalid GitHub username")
    result = {"schema_version": 1, "username": username,
              "fetched_at": datetime.now(timezone.utc).isoformat(), "complete": False,
              "pages": 0, "count": 0, "repositories": [],
              "pagination": {"page_counts": [], "terminal_next": True}}
    seen = set()
    next_url = f"https://api.github.com/users/{username}/starred?per_page=100&page=1"
    try:
        for page in range(1, 1001):
            request = urllib.request.Request(
                next_url,
                headers={"Accept": "application/vnd.github.star+json", "User-Agent": "project-router-skills-map"})
            with fetch(request, timeout=30) as response:
                items = json.load(response)
                link = response.headers.get("Link", "")
                next_links = re.findall(r'<([^>]+)>;\s*rel="next"', link)
                has_next = bool(next_links)
                if 'rel="next"' in link and not next_links:
                    raise ValueError("Malformed pagination link")
                if next_links:
                    parsed = urlparse(next_links[0])
                    if (parsed.scheme != "https" or parsed.netloc != "api.github.com" or
                        parsed.username or parsed.fragment or not re.fullmatch(
                            rf"/(?:users/{re.escape(username)}|user/[0-9]+)/starred", parsed.path)):
                        raise ValueError("Unexpected pagination target")
                    next_url = next_links[0]
            if not isinstance(items, list) or len(items) > 100:
                raise ValueError("Unexpected GitHub response")
            if not items and has_next:
                raise ValueError("Empty non-terminal page")
            for item in items:
                repo = item["repo"]
                if repo["id"] in seen:
                    raise ValueError("Duplicate repository across pages; retry a fresh scan")
                seen.add(repo["id"])
                result["repositories"].append({
                    "id": repo["id"], "full_name": repo["full_name"],
                    "description": repo.get("description") or "", "topics": repo.get("topics", []),
                    "default_branch": repo["default_branch"], "archived": repo["archived"],
                    "pushed_at": repo.get("pushed_at"), "starred_at": item["starred_at"],
                    "declared_license": (repo.get("license") or {}).get("spdx_id", "unknown"),
                })
            result["pages"] = page
            result["count"] = len(result["repositories"])
            result["pagination"]["page_counts"].append(len(items))
            result["pagination"]["terminal_next"] = has_next
            if not has_next:
                result["complete"] = True
                break
        if not result["complete"]:
            raise ValueError("Pagination limit reached")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["error"] = {"kind": type(exc).__name__}
        if isinstance(exc, urllib.error.HTTPError):
            result["error"].update(status=exc.code, retry_after=exc.headers.get("Retry-After"),
                                   rate_reset=exc.headers.get("X-RateLimit-Reset"))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = collect(args.username)
    # A failed collection never replaces the last successful output.
    target = args.output if result["complete"] else args.output.with_suffix(".partial.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(json.dumps({"status": "complete" if result["complete"] else "partial",
                      "pages": result["pages"], "count": result["count"], "output": str(target),
                      "error": result.get("error")}, ensure_ascii=False))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    sys.exit(main())
