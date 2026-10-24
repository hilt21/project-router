"""Check measurable constraints in saved agent output excerpts; not model evaluation."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
data = json.loads((root / "content.json").read_text())
characters = len("".join(data["wechat_body"].split()))
words = len(data["linkedin_body"].split())
assert 150 <= characters <= 250, characters
assert words <= 500, words
print(json.dumps({"wechat_non_whitespace_characters": characters, "linkedin_whitespace_words": words, "status": "passed"}))
