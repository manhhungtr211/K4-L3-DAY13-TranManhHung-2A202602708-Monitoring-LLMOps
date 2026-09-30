# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng vọt.
  2. **Logs:** Lọc `data/logs.jsonl` trong khoảng thời gian đó với điều kiện `latency_ms > 3000`, trích xuất một `correlation_id` tiêu biểu.
  3. **Traces:** Mở trace cùng `correlation_id` trên Langfuse, so sánh thời lượng các span `retrieval` và `generation` để xác định bước nào gây chậm trễ.
- Mitigation tạm thời: Dựa trên evidence thực tế để rollback prompt, chuyển sang model dự phòng nhẹ hơn, bật cache hoặc tạm thời tắt retriever nếu có lỗi timeout.
- Owner: `student-2A202602708`

---

## Alert 1

- Tên: `HighLatencyP99`
- Severity: `high`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts-latency`
- SLI/SLO liên quan: Primary SLO `fast_successful_requests` (latency P99 của `response_sent.latency_ms <= 3000ms`)
- Điều kiện và thời gian duy trì: `p99(latency_ms) > 3000ms` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng trải nghiệm độ trễ cao bất thường (> 3 giây), nguy cơ timeout giao diện web/chat, ảnh hưởng nghiêm trọng đến trải nghiệm hội thoại.
- Ba bước kiểm tra đầu tiên (Metrics → Logs → Traces):
  1. **Metrics:** Kiểm tra panel **Latency & TTFT** trên Dashboard runtime để xác định thời điểm bắt đầu tăng P99, kiểm tra xem TTFT có tăng theo hay chỉ tổng latency tăng.
  2. **Logs:** Truy vấn file `data/logs.jsonl` với bộ lọc: `event == "response_sent"` và `latency_ms > 3000`. Lấy ra 2–3 mẫu `correlation_id` gần nhất cùng thông tin `feature`, `session_id`.
  3. **Traces:** Mở Langfuse UI, tìm kiếm theo `correlation_id` vừa tìm được. Quan sát biểu đồ thác nước (waterfall):
     - Nếu span `retrieval` chiếm > 2500ms: Xác định vấn đề nằm ở vector database hoặc incident chậm vector search (`rag_slow`).
     - Nếu span `generation` chiếm > 2500ms: Kiểm tra token output tăng đột biến hoặc nhà cung cấp LLM bị nghẽn mạng.
- Mitigation tạm thời:
  - Nếu do retrieval chậm: Kích hoạt cache vector search hoặc disable incident (`python scripts/inject_incident.py --scenario rag_slow --disable`).
  - Nếu do LLM generation chậm: Giảm `max_tokens` của prompt hoặc tạm thời chuyển traffic sang model fallback có tốc độ phản hồi nhanh hơn.
- Owner: `SRE_Team`

---

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts-platform`
- SLI/SLO liên quan: Guardrail SLO `error_rate_pct_max <= 2%` và `retrieval_success_rate_pct_min >= 90%`
- Điều kiện và thời gian duy trì: `error_rate > 5%` liên tục trong 5 phút (hoặc retrieval error rate > 10%)
- Ảnh hưởng tới người dùng: Hệ thống trả về lỗi HTTP 500 hoặc thông báo lỗi hệ thống, người dùng không nhận được câu trả lời cho câu hỏi của mình.
- Ba bước kiểm tra đầu tiên (Metrics → Logs → Traces):
  1. **Metrics:** Mở panel **Retrieval Success Rate** và xem bảng mã lỗi (HTTP 5xx rate) trên Dashboard để định lượng tỷ lệ lỗi và số request bị ảnh hưởng.
  2. **Logs:** Lọc file `data/logs.jsonl` với điều kiện `event == "request_failed"` hoặc `tool_success == false`. Đọc trường `error_type` (ví dụ `RuntimeError: Vector store timeout`) và ghi lại `correlation_id`.
  3. **Traces:** Tra cứu `correlation_id` trên Langfuse, quan sát observation có trạng thái đỏ/lỗi (ERROR status) và đọc chi tiết `statusMessage` / stacktrace trong span.
- Mitigation tạm thời:
  - Nếu lỗi `Vector store timeout` (incident `tool_fail`): Kích hoạt chế độ trả lời fallback không dùng tài liệu (`retrieve()` fallback trả về tài liệu tĩnh hoặc câu trả lời mặc định).
  - Khởi động lại service hoặc rollback container về phiên bản ổn định gần nhất nếu phát hiện bug sau deployment.
- Owner: `Platform_Team`

---

## Alert 3

- Tên: `LowResponseQuality`
- Severity: `medium`
- Duration: `15m`
- Kênh thông báo: Slack `#k4-l3b-alerts-ai`
- SLI/SLO liên quan: Guardrail SLO `quality_score_avg_min >= 0.75`
- Điều kiện và thời gian duy trì: `p50(quality_score) < 0.6` kéo dài trong 15 phút
- Ảnh hưởng tới người dùng: Câu trả lời của chatbot bị cụt lủn, ảo giác (hallucination), không bám sát tài liệu tham khảo hoặc vi phạm chính sách hiển thị (bị gắn nhãn redacted quá nhiều).
- Ba bước kiểm tra đầu tiên (Metrics → Logs → Traces):
  1. **Metrics:** Kiểm tra panel **Quality Score** trên Dashboard để xác định xu hướng giảm bắt đầu từ mốc thời gian nào và có trùng với thời điểm cập nhật prompt mới hay không.
  2. **Logs:** Lọc các log `response_sent` có `quality_score < 0.6` trong `data/logs.jsonl`. Kiểm tra xem `doc_count` có bằng 0 không và đọc `answer_preview`.
  3. **Traces:** Mở Langfuse UI, kiểm tra metadata của các trace có quality score thấp:
     - So sánh metadata `prompt_name`, `prompt_version` và `prompt_label`.
     - Kiểm tra xem prompt vừa được cập nhật lên `candidate` (v2) hay do retriever trả về kết quả không khớp nội dung câu hỏi.
- Mitigation tạm thời:
  - Nếu chất lượng giảm do prompt mới: Thực hiện rollback ngay lập tức label `production` về phiên bản prompt ổn định trước đó (v1) trên Langfuse UI mà không cần sửa code.
  - Nếu do retrieval rỗng: Bổ sung context tài liệu chuẩn vào corpus kiến thức.
- Owner: `AI_Engineering_Team`
