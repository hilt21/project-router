"""Reject changes to release records that already exist in the comparison base."""
import argparse
import re
import subprocess


def check(base: str) -> list[str]:
    if not base or base == "0" * 40:
        return []
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("Expected full base SHA")
    subprocess.check_call(["git", "cat-file", "-e", f"{base}^{{commit}}"])
    changed = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=MDTR", base, "HEAD", "--", "releases"], text=True)
    return changed.splitlines()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="")
    args = parser.parse_args()
    violations = check(args.base)
    if violations:
        raise SystemExit("Immutable release records changed: " + ", ".join(violations))
    print("Release history check passed")
