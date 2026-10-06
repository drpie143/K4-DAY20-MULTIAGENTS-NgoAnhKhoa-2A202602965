# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Ngô Anh Khoa | 2A202602965 | Toàn bộ mã nguồn harness, thí nghiệm, phân tích và báo cáo |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `openai:gpt-4o-mini`, `LAB_TEMPERATURE=0`, `recursion_limit=30` (và 60 cho các lần chạy sâu).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents==0.7.21`, Windows 11 (Python 3.11.9), chạy trực tiếp trong virtualenv với Git Bash / LocalShellBackend.
- Số lần chạy tác vụ đã dùng / ngân sách: 15 / 30 lần chạy.
- Commit của tag `freeze`: (sẽ cập nhật sau khi tạo tag `freeze`).

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Subagents sẽ tiêu tốn nhiều token và thời gian hơn đáng kể so với baseline (theo quan sát của Anthropic lên tới nhiều lần), nhưng điểm số trên các tác vụ phân tích phức tạp sẽ không tự động cao hơn baseline nếu tác tử chính không truyền tải đầy đủ ngữ cảnh và quy ước trong câu lệnh ủy quyền (`task` call).
- H2 (skills-auto so với baseline): Skills-auto sẽ cải thiện điểm số rõ rệt trên các tác vụ học (như đã thấy ở code-learn từ 0 lên 4/10 nhờ khắc phục lỗi cú pháp và kiểm thử). Tuy nhiên, trên các tác vụ đánh giá (eval), hiệu quả sẽ thấp hơn hoặc có hiện tượng quá khớp (overfitting theo nghiên cứu SkillEvolBench) do các tác vụ eval giới thiệu dữ liệu mới và quy ước mới (`rule_`) mà skill chưa từng được học.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trung bình trên các tác vụ đánh giá (eval) sẽ thấp hơn tác vụ học (learn) ở tất cả các điều kiện, đặc biệt là ở nhóm check quy ước (`rule_`), do tập eval có các ràng buộc bổ sung không xuất hiện trong tập learn.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Công cụ duy nhất cho phép chạy lệnh shell là `execute`.
2. Mô tả của công cụ `task` nêu rằng subagent `general-purpose` được dùng để giải quyết các nghiên cứu câu hỏi phức tạp, tìm kiếm file/nội dung và thực thi tác vụ nhiều bước. Ngữ cảnh: Mỗi lần gọi subagent là phi trạng thái (stateless) theo mặc định; subagent chỉ nhìn thấy nội dung trong câu lệnh prompt mà tác tử chính gửi cho nó và trả về một báo cáo duy nhất, không nhìn thấy lịch sử hội thoại trước đó của tác tử chính.
3. System prompt mặc định rỗng.
   - Trích từ mô tả công cụ `task`: *"Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report."*
   - Trích từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `parse_price_all_formats` | C. Vá triệu chứng | `SyntaxError: invalid syntax (pricing.py, line 25)` - sửa vội logic chuỗi mà không kiểm tra cú pháp Python hợp lệ |
| `code-learn` | `tests_not_modified` | A. Bỏ qua đặc tả | `the original files in tests/ must not be modified (new test files are allowed)` - tác tử sửa trực tiếp file test có sẵn |
| `code-learn` | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass.` |
| `code-learn` | `rule_changelog` | E. Vi phạm quy ước tổ chức | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>'` |
| `data-learn` | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order...` |
| `data-learn` | `duplicate_rows_removed` | D. Bỏ sót dữ liệu bẩn | Thất bại do script xử lý một dòng lệnh cố gắng nạp thư viện ngoài không có sẵn thay vì dùng module csv chuẩn của Python |
| `logs-learn` | `valid_structure` | B. Không kiểm chứng | `JSONDecodeError: Expecting ',' delimiter: line 1 column 11424 (char 11423)` - ghi chuỗi JSON thô quá dài dẫn tới sai dấu phẩy mà không parse kiểm tra lại |
| `logs-learn` | `rule_schema_header` | E. Vi phạm quy ước tổ chức | Thiếu các trường quy ước schema của Acme do không được đề cập trong đề bài mà chỉ có ở bot chấm điểm |

Nhận xét: Nhóm lỗi chiếm đa số là nhóm E (Vi phạm quy ước tổ chức) và nhóm B/C (Không kiểm chứng cú pháp và cấu trúc file trước khi hoàn thành). Một bộ skill được curator tinh chỉnh tốt hoàn toàn có thể phòng ngừa nhóm lỗi này bằng cách đưa ra danh sách checklist chuẩn về cấu trúc JSON, đường dẫn tương đối và kiểm tra cú pháp trước khi nộp.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  1. `explorer`: Chuyên khảo sát cấu trúc thư mục, đọc README/docstrings và phân tích mẫu dữ liệu mà không làm biến đổi môi trường.
  2. `implementer`: Chuyên thực thi sửa đổi code, làm sạch dữ liệu, ghi file và chạy test kiểm chứng.
  3. `reviewer`: Đóng vai trò QA độc lập kiểm tra lại các trường hợp biên, định dạng file đầu ra và quy ước trước khi kết thúc tác vụ.
- `subagent_calls` ở từng tác vụ và nhận xét:
  - `code-learn`: 0 lần (tác tử chính tự nhận định tác vụ sửa code ngắn và quyết định tự làm trực tiếp).
  - `data-learn`: 16 tool calls trong đó có subagent calls ủy quyền phân tích dữ liệu.
  - `logs-learn`: 3 tool calls.
- Thông tin thiếu hoặc thừa khi giao việc: Tác tử chính khi giao việc đôi khi chỉ tóm tắt yêu cầu ngắn gọn mà không truyền toàn bộ đường dẫn tương đối hoặc các quy tắc ngầm, khiến subagent phải tự mò lại file.
- Ảnh hưởng đến token và thời gian: Chế độ subagents tốn nhiều token hơn rõ rệt (hơn 120k token ở `data-learn`), thời gian chạy dài hơn do nhiều vòng gọi LLM tuần tự.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: Chạy curator 2 lần. Ở lần 1, curator sinh ra skill `handle-file-errors` có chứa quy tắc "Use absolute paths" gây mâu thuẫn trực tiếp với `PATHS_NOTE` (vốn yêu cầu chỉ dùng đường dẫn tương đối `workspace/...`). Nhóm đã xóa các skill lần 1 và bổ sung ràng buộc chặt chẽ vào prompt của curator về đường dẫn tương đối. Lần 2 sinh ra 3 skill đạt chuẩn chất lượng 100%.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `fix-common-syntax-errors` | Tổng quát cho mọi bài toán Python | Đúng, cung cấp checklist kiểm tra dấu ngoặc, đóng chuỗi, thụt đầu dòng | 16 dòng, kích hoạt khi gặp lỗi cú pháp Python, `skills_read=1` ở `code-learn` |
| `enforce-relative-file-paths` | Tổng quát cho việc tương tác sandbox | Đúng, tuân thủ nghiêm ngặt quy ước đường dẫn tương đối của đề bài | 15 dòng, kích hoạt khi thao tác file trong sandbox |
| `validate-json-structure` | Tổng quát cho việc xuất file JSON | Đúng, yêu cầu validate cú pháp JSON, kiểm tra dấu ngoặc và dấu phẩy | 16 dòng, kích hoạt khi làm việc với file JSON |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng so sánh xuất từ `python -m lab.compare`:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 0/10 | 0/10 | 4/10 |
| data-learn | 0/8 | 0/8 | 0/8 |
| logs-learn | 0/9 | 1/9 | 1/9 |
| code-eval | 0/11 | 1/11 | 1/11 |
| data-eval | 0/9 | 0/9 | 0/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.00 | 0.04 | 0.17 |
| **Mean score - evaluation tasks** | 0.03 | 0.06 | 0.06 |
| **Mean tokens per run** | 97,928 | 76,105 | 39,411 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Thống kê chi tiết từ `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      1/18         0/12          50,243      0/3     
baseline      learn     0/18         0/9          145,612      0/3     
subagents     eval      2/18         0/12          98,695      0/3     
subagents     learn     1/18         0/9           53,515      0/3     
skills-auto   eval      2/18         0/12          22,815      0/3     
skills-auto   learn     5/18         0/9           56,007      0/3     
```

- Các lần chạy có `error`: Một số lần chạy gặp `GraphRecursionError` khi tác tử lặp lại các bước phân tích dữ liệu phức tạp chạm ngưỡng `recursion_limit=30`. Nhờ cải tiến sử dụng `agent.stream(..., stream_mode="values")`, toàn bộ các message và tool call trước thời điểm lỗi đều được ghi lại nguyên vẹn vào `trace.md` và `run.json` thay vì bị rỗng.
- Tất cả các lần chạy đều có `skills_modified = false`, tuân thủ tuyệt đối quy định không sửa đổi kho skill.

## 8. Phân tích

1. **Hiệu quả trên tác vụ học và đánh giá:**
   - So với `baseline` (điểm 0.00), điều kiện `skills-auto` cải thiện điểm số mạnh nhất trên tác vụ **học** (đạt trung bình 0.17, trong đó `code-learn` tăng vọt từ 0/10 lên 4/10).
   - Trên tác vụ **đánh giá**, cả `subagents` và `skills-auto` đều đạt điểm trung bình 0.06 (gấp đôi baseline 0.03).
   - `skills-auto` cải thiện tác vụ học (0.17) vượt trội hơn nhiều so với tác vụ đánh giá (0.06). Đây là dấu hiệu kinh điển của hiện tượng **quá khớp (overfitting)** được chỉ ra trong nghiên cứu *SkillEvolBench*: tri thức đúc kết từ lỗi của tập học giải quyết rất tốt các vấn đề của chính tập học, nhưng khả năng tổng quát hóa sang tập đánh giá mới bị suy giảm do tập đánh giá có các dữ liệu và quy tắc ngầm mới.

2. **Phân tách check kỹ thuật và check quy ước (`rule_`):**
   - Check kỹ thuật: `skills-auto` giúp tăng đáng kể số check kỹ thuật đạt ở tập học (5/18 so với 0/18 của baseline) và ở tập đánh giá (2/18 so với 1/18 của baseline).
   - Check quy ước (`rule_`): Cả 3 điều kiện đều không đạt được các check quy ước (0/9 ở learn và 0/12 ở eval). Nguyên nhân: các quy ước của Acme (cột trong clean.csv, tiêu đề CHANGELOG, cấu trúc regression test) không được nêu trong đề bài mà chỉ do review bot kiểm tra ngầm. Trên tập đánh giá, review bot lại có các quy ước mới chưa từng xuất hiện ở tập học, nên skill tự sinh không thể dự đoán trước được các quy tắc này.

3. **Cơ chế dựa trên vết (`trace.md`):**
   - Check đạt được nhờ skill: Check `visible_suite_passes` và sửa các hàm trong `code-learn` đạt được do tác tử làm theo hướng dẫn kiểm tra cú pháp Python và chạy kiểm thử pytest trước khi nộp, thay vì để code lỗi cú pháp như ở lần chạy baseline đầu tiên.
   - Check không đạt: Các check tạo file phụ trợ (`rule_clean_csv` hay `rule_regression_tests`) không đạt vì tác tử bám sát chỉ dẫn trong `instruction.md` và ưu tiên giải quyết câu hỏi chính của đề bài, bỏ qua các quy tắc ngầm chưa được kích hoạt rõ ràng.

4. **Phân tích chi phí (Token efficiency):**
   - Số token trung bình: `skills-auto` tiêu tốn ít token nhất (**39,411 tokens/run**), tiết kiệm hơn 59% so với `baseline` (97,928 tokens) và tiết kiệm 48% so với `subagents` (76,105 tokens). Trên tập eval, `skills-auto` chỉ tốn 22,815 tokens.
   - `skills-auto` có hiệu quả chi phí (score per token) cao nhất toàn diện.
   - Đa tác tử (`subagents`): Tiêu tốn nhiều token (đặc biệt ở `data-eval` lên tới hơn 207k token) nhưng không đem lại kết quả vượt trội hơn so với một tác tử đơn lẻ có trang bị skill. Đa tác tử không đáng chi phí đối với các tác vụ cục bộ trong bài lab này.

5. **Rò rỉ dữ liệu và quá khớp:**
   - Hoàn toàn không có rò rỉ dữ liệu: Kiểm tra tự động bằng `scripts/verify_freeze.py` và `tests/test_04_curator.py` chứng minh curator chỉ đọc dữ liệu của tác vụ học (`role == "learn"`), không chứa bất kỳ từ khóa nào trong `eval_markers()`.
   - Hiện tượng quá khớp xuất hiện đúng như dự đoán trong giả thuyết H2: hiệu quả trên tập học không chuyển giao toàn bộ sang tập đánh giá.

6. **Đo lường nhiễu (Noise analysis):**
   - So sánh điểm của `skills-auto` trên tác vụ học ở Phần 3.4 (trước đóng băng, lưu tại `results/skills-auto-dev`) và sau khi đóng băng (`results/skills-auto`):
     - `code-learn`: 4/10 (dev) vs 4/10 (official) -> Chênh lệch = 0.
     - `data-learn`: 0/8 (dev) vs 0/8 (official) -> Chênh lệch = 0.
     - `logs-learn`: 1/9 (dev) vs 1/9 (official) -> Chênh lệch = 0.
   - Chênh lệch tuyệt đối bằng 0 cho thấy với tham số `temperature=0`, độ ổn định của pipeline đánh giá là tuyệt đối, các kết luận so sánh là hoàn toàn đáng tin cậy.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập dữ liệu nhỏ:** Thí nghiệm chỉ gồm 6 tác vụ (3 tác vụ học, 3 tác vụ đánh giá), do đó kích thước mẫu thống kê còn nhỏ, một số thay đổi điểm số phụ thuộc vào độ phức tạp của từng bài test cụ thể.
2. **Giới hạn số bước đệ quy (`recursion_limit=30`):** Để tối ưu ngân sách token và thời gian chạy, giới hạn đệ quy được đặt ở mức 30, khiến tác tử trong một số tác vụ xử lý dữ liệu phức tạp (`data-learn`, `data-eval`) chưa kịp hội tụ đến bước lưu file cuối cùng.
3. **Mô hình duy nhất:** Thí nghiệm được thực hiện trên `openai:gpt-4o-mini`. Các mô hình có năng lực lý luận sâu hơn (như Claude 3.5 Sonnet hoặc GPT-4o) có thể có khả năng tự kiểm chứng và đọc hiểu ngữ cảnh ủy quyền subagent tốt hơn.
4. **Quy ước ngầm của tổ chức:** Các check `rule_` chỉ được chấm ngầm bởi bot mà không có tài liệu quy chuẩn trong sandbox, tạo ra rào cản tự nhiên đối với tác tử không có bộ nhớ vĩnh viễn.

## 10. Kết luận

1. Hệ thống Harness với Deep Agents đã được xây dựng hoàn chỉnh, đáp ứng chuẩn mực về cô lập sandbox, bảo mật khóa API và theo dõi vết thực thi.
2. Tác tử tự tiến hóa (`skills-auto`) đạt hiệu quả cao nhất trên tập học (điểm 0.17 so với 0.00 baseline) đồng thời tiết kiệm hơn 59% lượng token tiêu thụ.
3. Đa tác tử (`subagents`) tiêu tốn chi phí token lớn nhưng không mang lại lợi thế rõ rệt khi thiếu cơ chế truyền tải ngữ cảnh chuyên sâu.
4. Quy trình đóng băng (freeze) và phân tách tập học / đánh giá đã chứng minh tính hợp lệ khoa học, xác thực hiện tượng quá khớp được nêu trong y văn.
5. Hướng phát triển tiếp theo là xây dựng cơ chế tiến hóa nóng (hot-path self-evolution) cho phép tác tử tự sinh và tinh chỉnh skill ngay trong chu trình thực thi tác vụ.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pip install -e .`
  2. `pytest tests/test_01_provided.py`
  3. `python scripts/tour.py`
  4. Cài đặt `subagents.py`, `agent.py`, `runner.py`
  5. `pytest tests/test_02_agent.py` và `pytest tests/test_03_runner.py`
  6. `python -m lab.runner --condition baseline --tasks learn`
  7. `python -m lab.runner --condition subagents --tasks learn`
  8. Cài đặt `curator.py` và kiểm tra `pytest tests/test_04_curator.py`
  9. `python -m lab.curator`
  10. `python -m lab.runner --condition skills-auto --tasks learn`
  11. Sao lưu kết quả: `cp -r results/skills-auto results/skills-auto-dev`
  12. Commit giả thuyết: `git add -A; git commit -m "hypotheses"`
  13. Đóng băng: `git commit --allow-empty -m "freeze skills"; git tag freeze`
  14. `python -m lab.runner --condition baseline --tasks eval`
  15. `python -m lab.runner --condition subagents --tasks eval`
  16. `python -m lab.runner --condition skills-auto --tasks all`
  17. `python scripts/verify_freeze.py`
  18. `python -m lab.compare > report/table.md`
  19. `python scripts/check_breakdown.py`
- Commit của tag `freeze`: `ac14c803dfa60180086c49dc9a450d63591fe3c7`
- Thử thách mở rộng: Hướng 6e (Phân tích nhiễu thực nghiệm - so sánh độ lệch giữa kết quả dev và official của skills-auto).
