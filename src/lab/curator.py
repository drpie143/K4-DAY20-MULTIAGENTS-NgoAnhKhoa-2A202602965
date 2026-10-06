"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import re
from pathlib import Path

from .tasks import eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


import json

from .model import make_model
from .tasks import ROOT


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    target_out_dir = Path(out_dir) if out_dir is not None else (ROOT / "skills" / "auto")

    runs = []
    cond_dir = Path(results_dir) / source_condition
    if cond_dir.exists():
        for p in sorted(cond_dir.iterdir()):
            run_file = p / "run.json"
            if run_file.exists():
                try:
                    r = json.loads(run_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if r.get("role") != "learn":
                    continue

                failed = [
                    (c.get("name"), c.get("detail", ""))
                    for c in r.get("checks", [])
                    if not c.get("passed")
                ]

                trace_file = p / "trace.md"
                trace_content = trace_file.read_text(encoding="utf-8")[-6000:] if trace_file.exists() else ""
                runs.append({
                    "task": r.get("task", p.name),
                    "failed": failed,
                    "trace": trace_content,
                })

    has_failures = any(len(r["failed"]) > 0 for r in runs)
    if not has_failures:
        print("Warning: no failed checks found in learning tasks.")
        return []

    prompt_lines = [
        "You are writing reusable SKILL files for an engineering assistant.",
        "Below are failed checks (check names and the review bot feedback) and execution traces from learning tasks.",
        f"Identify common procedural mistakes and write up to {max_skills} concise skills to prevent them on new tasks of the same kind.",
        "",
        "Rules:",
        "- `name`: MUST consist ONLY of lowercase letters, numbers, and hyphens (regex: ^[a-z0-9]+(-[a-z0-9]+)*$). Example: 'fix-code-regressions', 'acme-data-cleaning'. NEVER use uppercase or CamelCase!",
        "- `description`: One concise sentence explaining WHEN to use the skill (e.g. 'Use when fixing bugs in Python packages to ensure tests pass and conventions are met.').",
        "- The body must be under 40 lines of actionable imperative checklist rules.",
        "- Emphasize that all file paths MUST be relative (e.g. workspace/..., not starting with '/').",
        "- Do not mention specific task IDs (like code-learn or data-learn) or hardcoded numerical solutions.",
        "- Format each skill strictly as follows:",
        "=== SKILL: <name> ===",
        "---",
        "name: <name>",
        "description: Use when <trigger condition>",
        "---",
        "# Title",
        "",
        "<checklist instructions>",
        "=== END ===",
        "",
        "Learning task run failures and traces:",
    ]

    for r in runs:
        prompt_lines.append(f"\nTask: {r['task']}")
        prompt_lines.append("Failed checks:")
        for name, detail in r["failed"]:
            prompt_lines.append(f"- {name}: {detail}")
        if r["trace"]:
            prompt_lines.append(f"Trace summary:\n{r['trace']}\n")

    prompt = "\n".join(prompt_lines)
    chat_model = model or make_model()
    response = chat_model.invoke(prompt)
    reply = response.content if hasattr(response, "content") else str(response)

    written = []
    for name, text in parse_skill_blocks(reply):
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        skill_file = target_out_dir / name / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(text + "\n", encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
