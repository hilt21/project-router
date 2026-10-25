"""Check measurable constraints in saved agent output excerpts; not model evaluation."""
import json
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
data = json.loads((root / "content.json").read_text())
characters = len("".join(data["wechat_body"].split()))
words = len(data["linkedin_body"].split())
assert 150 <= characters <= 250, characters
assert words <= 500, words
print(json.dumps({"wechat_non_whitespace_characters": characters, "linkedin_whitespace_words": words, "status": "passed"}))

manifest = json.loads((root / "academic/manifest.json").read_text())
assert manifest["real_work_fresh_chat"] == "not-run"
assert manifest["model_independence"] == "not-established"
for case in manifest["cases"]:
    for item in case["files"].values():
        path = root / "academic" / item["path"]
        assert path.resolve().is_relative_to((root / "academic").resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], item["path"]
print(json.dumps({"layer": "probe-artifact-integrity", "cases": len(manifest["cases"]),
                  "status": "passed", "semantic_correctness": "not-verified"}))
