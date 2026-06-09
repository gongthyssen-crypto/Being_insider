from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.runtime_settings import get_runtime_settings, update_runtime_settings
from app.schemas import RuntimeSettingsUpdate


class RuntimeSettingsTests(unittest.TestCase):
    def test_updates_are_applied_and_clamped(self) -> None:
        original = get_runtime_settings()

        try:
            updated = update_runtime_settings(
                RuntimeSettingsUpdate(
                    deepseek_max_tokens=9000,
                    deepseek_thinking_enabled=False,
                    turn_knowledge_max_matches=7,
                    turn_knowledge_max_excerpt_chars=1500,
                )
            )

            self.assertEqual(8192, updated.deepseek_max_tokens)
            self.assertFalse(updated.deepseek_thinking_enabled)
            self.assertEqual(7, updated.turn_knowledge_max_matches)
            self.assertEqual(1500, updated.turn_knowledge_max_excerpt_chars)
        finally:
            update_runtime_settings(RuntimeSettingsUpdate(**original.model_dump()))


if __name__ == "__main__":
    unittest.main()
