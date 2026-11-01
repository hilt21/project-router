"""Static contracts for independently generated multi-image content.

These do not run the actual image generator. Real tool and visual QA must be
recorded separately.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class MultiImageDeliveryContractTests(unittest.TestCase):
    def test_wechat_explicit_count_overrides_default(self):
        text = read("rules/content-wechat.md")
        self.assertIn("用户明确指定 N 张", text)
        self.assertIn("严格以 N 张为交付目标", text)
        self.assertIn("封面 1 张、主题 5 张", text)
        self.assertIn("20 个字符", text)

    def test_independent_generation_and_no_crop_repair(self):
        rules = read("rules/content.md")
        flow = read("workflows/content.md")
        craft = read("skills/craft-channel-content/SKILL.md")
        for source in (rules, flow, craft):
            self.assertIn("image_id", source)
            self.assertIn("独立", source)
            self.assertIn("n=1", source)
            self.assertIn("裁切", source)
        self.assertIn("6 次独立单图生成", flow)

    def test_missing_or_invalid_images_never_pass(self):
        flow = read("workflows/content.md")
        verifier = read("skills/verify-delivery/SKILL.md")
        for phrase in ("图片数量", "画布独立性", "文字清晰度", "重做该图"):
            self.assertIn(phrase, flow)
        for phrase in ("N/N", "unknown", "failed", "partial", "拼版"):
            self.assertIn(phrase, verifier)

    def test_collage_only_with_explicit_intent_and_brief_only_is_readonly(self):
        rules = read("rules/content.md")
        flow = read("workflows/content.md")
        self.assertIn("用户明确要求拼图或总览图时", rules)
        self.assertIn("用户仅要求视觉 Token 时停止在方案阶段", flow)


if __name__ == "__main__":
    unittest.main()
