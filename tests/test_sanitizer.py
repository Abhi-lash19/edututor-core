# tests/test_sanitizer.py
from edututor.core.sanitizer import strip_code_blocks


def test_strip_code_blocks_removes_fenced_and_inline():
    s = "Here is code:\n```py\nprint('hi')\n```\nAnd inline `x = 1` end."
    out = strip_code_blocks(s)
    assert "[code omitted" in out
    assert "[code omitted]" in out
