"""Conservative 20-character preflight for WeChat image-post titles.

Counts Unicode code points, including letters, punctuation, digits and spaces.
Complex emoji and platform-specific grapheme handling may differ; avoid them
or leave additional headroom when preparing publication titles.
"""

import argparse

MAX_TITLE_CHARS = 20


def count_title_characters(title: str) -> int:
    return len(title)


def is_publishable_title(title: str) -> bool:
    return (
        bool(title.strip())
        and "\n" not in title
        and "\r" not in title
        and count_title_characters(title) <= MAX_TITLE_CHARS
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("titles", nargs="+", help="One or more quoted candidate titles")
    args = parser.parse_args()

    all_pass = True
    for title in args.titles:
        passed = is_publishable_title(title)
        all_pass = all_pass and passed
        status = "PASS" if passed else "FAIL"
        print(f"{status} {count_title_characters(title)}/{MAX_TITLE_CHARS} {title}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
