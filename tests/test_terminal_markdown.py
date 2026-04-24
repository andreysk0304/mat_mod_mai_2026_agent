from __future__ import annotations

import unittest

from agent.terminal_markdown import render_markdown


class TerminalMarkdownTests(unittest.TestCase):
    def test_renders_markdown_table_as_aligned_terminal_table(self) -> None:
        rendered = render_markdown(
            "\n".join(
                [
                    "| Task | Hours | Value |",
                    "|---|---:|---:|",
                    "| README | 1 | 3 |",
                    "| Screencast | 3 | 8 |",
                ]
            ),
            enable_ansi=False,
        )

        self.assertIn("+------------+-------+-------+", rendered)
        self.assertIn("| Task       | Hours | Value |", rendered)
        self.assertIn("| README     |     1 |     3 |", rendered)
        self.assertIn("| Screencast |     3 |     8 |", rendered)

    def test_renders_bold_and_inline_code_with_ansi(self) -> None:
        rendered = render_markdown("**Итог:** использовать `plan_optimizer`.", enable_ansi=True)

        self.assertIn("\033[1mИтог:\033[0m", rendered)
        self.assertIn("\033[36mplan_optimizer\033[0m", rendered)

    def test_strips_markdown_when_ansi_disabled(self) -> None:
        rendered = render_markdown("**Итог:** использовать `plan_optimizer`.", enable_ansi=False)

        self.assertEqual(rendered, "Итог: использовать plan_optimizer.")


if __name__ == "__main__":
    unittest.main()
