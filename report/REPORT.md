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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
