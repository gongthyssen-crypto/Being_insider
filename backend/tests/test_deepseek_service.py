from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.json_repair import parse_json_with_repair


class DeepSeekRepairTests(unittest.TestCase):
    def test_recovers_from_unescaped_quotes_in_string_fields(self) -> None:
        sample = """
        {
          "ai_narration": "袁世凯召来幕僚，说"此事当缓图"，众人一时沉默。",
          "outcome_summary": "朝野开始重新评估你的意图。",
          "world_update": "驻朝布局出现新的试探。",
          "next_prompt_hint": "你可以选择继续试探或稳住盟友。",
          "suggested_options": [
            {"id": "steady", "label": "稳住朝局", "brief": "先稳住军心", "strategic_hint": "避免节外生枝"},
            {"id": "probe", "label": "继续试探", "brief": "向朝鲜宫廷施压", "strategic_hint": "换取主动"},
            {"id": "ally", "label": "拉拢盟友", "brief": "争取关键支持", "strategic_hint": "补强后路"}
          ],
          "ending": null
        }
        """

        parsed = parse_json_with_repair(sample)

        self.assertIn('说"此事当缓图"', parsed["ai_narration"])
        self.assertEqual("朝野开始重新评估你的意图。", parsed["outcome_summary"])
        self.assertEqual("驻朝布局出现新的试探。", parsed["world_update"])
        self.assertEqual("你可以选择继续试探或稳住盟友。", parsed["next_prompt_hint"])
        self.assertEqual(3, len(parsed["suggested_options"]))
        self.assertIsNone(parsed["ending"])


if __name__ == "__main__":
    unittest.main()
