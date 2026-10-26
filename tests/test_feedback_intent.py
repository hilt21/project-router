"""Static contract checks for conditional feedback routing.

These assertions verify instruction presence and scope only. They cannot
demonstrate that a hosted agent detects or files feedback at runtime.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class FeedbackIntentContractTests(unittest.TestCase):
    def test_checkpoint_runs_per_user_message_and_after_new_failure(self):
        bootstrap = read("BOOTSTRAP.md")
        shared = read("rules/shared.md")
        self.assertIn("每条新的用户消息", bootstrap)
        self.assertIn("执行后出现新的实质偏差时再检查一次", bootstrap)
        self.assertIn("每条新用户消息先做反馈意图检查", shared)
        self.assertIn("不依赖“反馈”等关键词", bootstrap)

    def test_conditional_skill_uses_same_snapshot(self):
        bootstrap = read("BOOTSTRAP.md")
        protocol = read("docs/PROTOCOL.md")
        registry = read("registry/skills.yaml")
        self.assertIn("skills/capture-router-feedback/SKILL.md", bootstrap)
        self.assertIn("feedback/README.md", bootstrap)
        self.assertIn("同一源 SHA", bootstrap)
        self.assertIn("反馈 skill 不属于每次执行包的必需技能", protocol)
        self.assertIn("capture-router-feedback:", registry)
        self.assertNotIn("capture-router-feedback", read("routes/content-studio.md"))

    def test_negative_cases_and_scoped_authorization(self):
        policy = read("feedback/README.md")
        for phrase in ("对当前一篇文案的临时改写", "未核实的推测",
                       "不产生持久反馈", "不再为同一问题创建第二条 Issue",
                       "无授权时止于草稿", "项目 ID"):
            self.assertIn(phrase, policy)
        self.assertIn("不得上传完整对话", policy)
        self.assertIn("不依赖关键词自动分类器", read("docs/PROTOCOL.md"))

    def test_status_and_memory_distinction_are_observable(self):
        policy = read("feedback/README.md")
        for status in ("drafted", "linked-existing", "filed", "blocked"):
            self.assertIn(status, policy)
        self.assertIn("ChatGPT Memory", read("BOOTSTRAP.md"))
        self.assertIn("Memory 提示不作为仓库写入证据", read("docs/PROTOCOL.md"))
        self.assertIn("真实新对话", read("docs/WORK_ACCEPTANCE.md"))
        self.assertIn("not-run", read("docs/WORK_ACCEPTANCE.md"))


if __name__ == "__main__":
    unittest.main()
