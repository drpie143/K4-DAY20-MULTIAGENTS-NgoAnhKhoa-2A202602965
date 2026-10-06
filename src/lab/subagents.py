"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    """
    return [
        {
            "name": "explorer",
            "description": "Use when you need to inspect the workspace, examine data/log samples, read docstrings or specifications, and understand root causes without making any modifications.",
            "system_prompt": "You are a research and exploration specialist. Read and inspect files, search for patterns, analyze error traces and docstrings, and report precise facts back to the supervisor. Never modify or create files.",
        },
        {
            "name": "implementer",
            "description": "Use when you need to implement bug fixes, clean tabular data, parse logs into target formats, and execute tests to verify changes.",
            "system_prompt": "You are an implementation specialist. Perform precise file edits and run tests or verification scripts using the shell to ensure correctness against task specifications. Report summary of changes and test outcomes.",
        },
        {
            "name": "reviewer",
            "description": "Use when implementation is finished to independently audit the workspace, verify output format and edge cases, and ensure compliance with instructions before completing the task.",
            "system_prompt": "You are an independent QA and code reviewer. Verify edge cases, validate schema/output files, confirm that common conventions and instructions are strictly met, and report any remaining issues.",
        },
    ]
