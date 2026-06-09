from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.content import get_scenario_seed
from app.deepseek_service import request_turn_resolution
from app.json_repair import parse_json_with_repair
from app.schemas import ScenarioSeed, SessionState


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

    @patch("app.deepseek_service.is_deepseek_configured", return_value=True)
    @patch("app.deepseek_service._request_completion")
    def test_retries_without_knowledge_when_first_response_is_truncated(
        self,
        mock_request_completion,
        _mock_is_configured,
    ) -> None:
        mock_request_completion.side_effect = [
            {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": '{"ai_narration":"x","suggest'},
                        "finish_reason": "length",
                    }
                ],
                "usage": {"completion_tokens": 1800},
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "ai_narration": "narration",
                                    "outcome_summary": "outcome",
                                    "world_update": "update",
                                    "next_prompt_hint": "hint",
                                    "suggested_options": [],
                                    "ending": None,
                                },
                                ensure_ascii=False,
                            ),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"completion_tokens": 500},
            },
        ]

        seed = ScenarioSeed(**get_scenario_seed("yuan_shikai_korea"))
        session = SessionState(**json.loads(
            """{
              "session_id": "test-session",
              "scenario_id": "yuan_shikai_korea",
              "status": "active",
              "turn_index": 1,
              "created_at": "2026-06-09T05:06:51.099664Z",
              "updated_at": "2026-06-09T05:07:55.525227Z",
              "world_summary": {
                "time_label": "清末 甲午战前的朝鲜 · 第 1 回合后",
                "location": "朝鲜风云：袁世凯与甲午前夜",
                "situation": "当前核心任务仍是：在不提前引爆中日正面摊牌的前提下，维持清廷在朝鲜的实际影响力。",
                "pressure_points": [
                  "若对朝鲜王室压得太重、对日本试探判断失误，局势会迅速失控。",
                  "你的决定更像一次务实调度。",
                  "需要继续平衡历史背景约束与现实行动空间。"
                ],
                "recent_shift": "局势已经出现新的偏移。"
              }
            }"""
        ))

        resolved = request_turn_resolution(seed, session, [], "继续")

        self.assertEqual("narration", resolved["ai_narration"])
        self.assertEqual("outcome", resolved["outcome_summary"])
        self.assertEqual("update", resolved["world_update"])
        self.assertEqual("hint", resolved["next_prompt_hint"])
        self.assertEqual(2, mock_request_completion.call_count)


if __name__ == "__main__":
    unittest.main()
