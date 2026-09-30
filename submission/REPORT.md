# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Trần Mạnh Hùng
- **MSSV:** 2A202602708
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/manhhungtr211/K4-L3-DAY13-TranManhHung-2A202602708-Monitoring-LLMOps
- **Commit SHA cuối:** *(Cập nhật sau commit cuối)*
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602708`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Error: data\logs.jsonl not found | 100/100 | Đã hoàn thành cấu hình structlog và PII scrubbing chuẩn schema |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel có trong dashboard contract | HỢP LỆ: 6/6 panel | Đầy đủ 6 panel theo contract `config/dashboard.yaml` |
| `pytest` | 2 errors (ModuleNotFoundError) | 25 passed | Toàn bộ 25 unit test pass bao gồm PII, prompt và tracing adapter |
| Số traces hợp lệ | 0 | 19+ traces | Đầy đủ cây quan sát root agent, retrieval span và generation |
| Số PII leak | Chưa đo | 0 | Scrubbing triệt để email, phone VN, CCCD, credit card |
| Latency P95 / TTFT P95 | P95: 1363ms / TTFT: 50ms | Challenge: 3631ms / TTFT: 50ms | Phát hiện chính xác độ trễ do incident `rag_slow` |
| Retrieval success rate | 100% | 100% | Retrieval hoạt động ổn định trong suốt quá trình test |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  Được Middleware `CorrelationIdMiddleware` kiểm tra trong header `X-Correlation-ID` của request gửi đến; nếu chưa có thì tự sinh mới bằng `uuid.uuid4().hex[:8]` theo định dạng `req-<hex>`. Giá trị này được lưu vào `request.state.correlation_id`, sau đó dùng `structlog.contextvars.bind_contextvars` để tự động đưa vào toàn bộ các dòng log của request và truyền vào metadata của trace trên Langfuse.

- **Các metadata được ghi vào structured log:**
  Mỗi dòng log JSON có các trường chuẩn: `ts` (ISO 8601 UTC), `level`, `service`, `event`, `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`. Với event `response_sent` bổ sung thêm các số liệu định lượng: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và `payload.answer_preview`.

- **Cách bảo đảm PII được scrub trước khi ghi:**
  Xây dựng module `app/pii.py` với hàm `mask_pii()` dùng regex để phát hiện và thay thế các thông tin nhạy cảm: email (`[REDACTED_EMAIL]`), số điện thoại Việt Nam (`[REDACTED_PHONE_VN]`), số CCCD 12 số (`[REDACTED_CCCD]`), số thẻ tín dụng 16 số (`[REDACTED_CREDIT_CARD]`). User ID được băm một chiều SHA-256 rút gọn 12 ký tự (`hash_user_id`), và nội dung tin nhắn được trích lược tối đa 80 ký tự (`summarize_text`) sau khi scrub.

- **Cách kiểm chứng kết quả:**
  Chạy test suite `tests/test_pii.py` và script `scripts/validate_logs.py data/logs.jsonl` đạt 100/100 điểm tuyệt đối; kiểm tra trực tiếp file log không có PII dạng raw text.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  Cấu hình `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` trỏ đến project cá nhân `day13-k4-l3b-2A202602708` trên `https://cloud.langfuse.com`. Traces hiển thị trên UI có `user_id` hash và `metadata.correlation_id` khớp với request gửi từ máy local.

- **Cấu trúc root/retrieval/generation observations:**
  ```text
  day13-agent-request
  └── lab-agent-run (type: agent - root observation, capture_input=False, capture_output=False)
      ├── retrieval (type: span - child observation tìm tài liệu context)
      └── generation (type: generation - child observation gọi LLM, có model, usage_details, cost_details)
  ```

- **Cách nối trace với log:**
  Đưa `correlation_id` vào `metadata` của Langfuse trace thông qua `propagate_attributes(metadata={"correlation_id": correlation_id, ...})`. Khi tra cứu log có `correlation_id`, ta filter trên Langfuse UI theo `Metadata -> correlation_id` để mở đúng trace tương ứng.

- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (labels: `baseline`, ban đầu gắn `production`)
- **Version/label candidate:** Version 2 (label: `candidate`)
- **Trace ID của mỗi version:**
  - Version 1 (`baseline`): `0ca4cf368f52afc8eb5b4137cd828d5a`
  - Version 2 (`candidate`): `b96d65724927ac1a6392b7c8ae5c3263`
  - Version 2 sau khi promote `production`: `6969638a0baf6e5c07c1ee297101b6ee`
  - Version 1 sau khi rollback `production`: `7ea1ecd2d4534c8d416da74c3ee6728d`
- **Cách promote và rollback `production`:**
  - Promote: Trên Langfuse UI (hoặc API `client.api.prompt_version.update`), chuyển nhãn `production` từ Version 1 sang Version 2.
  - Rollback: Khi phát hiện hồi quy chất lượng hoặc sự cố, gỡ nhãn `production` khỏi Version 2 và gán lại cho Version 1. Ứng dụng tự động nạp phiên bản prompt mới theo nhãn `production` mà không cần sửa code hay deploy lại service.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  Đủ 6 panel theo contract `config/dashboard.yaml`:
  1. `Latency & TTFT (ms)`: Theo dõi độ trễ tổng và thời gian sinh token đầu tiên kèm đường SLO 3000ms.
  2. `Traffic (Req/min)`: Lưu lượng yêu cầu theo từng phút.
  3. `Retrieval Success Rate (%)`: Tỷ lệ thành công của khâu tìm kiếm context kèm đường SLO 90%.
  4. `Cumulative Cost (USD)`: Chi phí tích lũy theo thời gian.
  5. `Tokens Usage`: Số lượng token đầu vào (input) và đầu ra (output).
  6. `Quality Score`: Điểm chất lượng trung bình kèm đường SLO 0.75.

- **SLO và lý do chọn:**
  Primary SLO `fast_successful_requests` với mục tiêu 99.5% trong cửa sổ 28 ngày (`latency_ms <= 3000ms`). Lý do: Baseline đo được cho thấy P50 ≈ 500ms, P95 ≈ 1363ms < 2000ms. Ngưỡng 3000ms đảm bảo phản hồi nhanh cho người dùng và đủ nhạy để phát hiện sự cố tắc nghẽn (như incident `rag_slow` gây trễ >2.5s).

- **Cách tính error budget:**
  Mục tiêu SLO là 99.5% trong 28 ngày, nghĩa là error budget là `100% - 99.5% = 0.5%`. Với khối lượng 10,000 requests, tối đa `10,000 * 0.5% = 50 requests` được phép chậm (> 3000ms) hoặc thất bại. Nếu vượt quá 50 requests, ngân sách lỗi cạn kiệt và cần dừng phát hành tính năng mới.

- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP99`: `latency_p99 > 3000ms` kéo dài 5 phút (High severity) -> [docs/alerts.md#alert-1](../docs/alerts.md#alert-1).
  2. `HighErrorRate`: `error_rate > 5%` kéo dài 5 phút (Critical severity) -> [docs/alerts.md#alert-2](../docs/alerts.md#alert-2).
  3. `LowResponseQuality`: `quality_score_p50 < 0.6` kéo dài 15 phút (Medium severity) -> [docs/alerts.md#alert-3](../docs/alerts.md#alert-3).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-30 23:38 – 23:45 (+07:00)
- **Triệu chứng từ metrics:**
  Panel **Latency & TTFT** trên Dashboard tăng đột biến: Latency P95 tăng vọt từ baseline ~1363ms lên **3631ms** (vượt ngưỡng cho phép 2000ms). Trong khi đó, metric TTFT (Time to First Token) vẫn duy trì ổn định ở mức **50ms**, chứng minh LLM không bị trễ mà điểm nghẽn nằm ở khâu tiền xử lý trước khi gọi LLM.
- **Log line và correlation ID liên quan:**
  Dòng log trong `data/logs.jsonl`:
  `{"service": "api", "latency_ms": 3631, "ttft_ms": 50, "tool_name": "retrieval", "tool_success": true, "event": "response_sent", "feature": "monitoring", "correlation_id": "req-9b19fefc", "level": "info", "ts": "2026-09-30T16:40:32.945490Z"}`
  Các request khác cùng nhóm challenge bị ảnh hưởng gồm: `req-b90af9e0` (2889ms), `req-632458df` (2887ms), `req-db54db2b` (2887ms), `req-8973fd14` (2890ms).
- **Trace ID và span gây ảnh hưởng:**
  Tra cứu `correlation_id: req-9b19fefc` trên Langfuse cho thấy span **`retrieval`** mất **~2500ms** (chiếm hơn 90% tổng thời gian request), trong khi span `generation` chỉ mất ~150ms.
- **Root cause:**
  Incident `rag_slow` được kích hoạt trên hệ thống (mô phỏng vector database bị quá tải hoặc mạng chập chờn khi truy vấn cơ sở dữ liệu tri thức), gây trễ nhân tạo 2.5s trong hàm `retrieve()` cho các câu hỏi thuộc nhóm `monitoring`.
- **Fix action:**
  Vô hiệu hóa incident bằng lệnh `python scripts/inject_incident.py --scenario rag_slow --disable`. Bổ sung timeout 1.5s cho module retrieval và fallback trả về tài liệu tĩnh để không làm gián đoạn toàn bộ request.
- **Preventive measure:**
  Thiết lập alert cảnh báo sớm khi P95 retrieval latency > 1500ms; áp dụng bộ nhớ đệm ngữ nghĩa (semantic caching) cho các câu hỏi phổ biến để giảm tải truy vấn trực tiếp vào vector database.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  Tách biệt hoàn toàn `correlation_id` (quản lý ở tầng ứng dụng/log) và `trace_id` (quản lý ở tầng telemetry), đồng thời liên kết chúng thông qua trường `metadata` của Langfuse trace. Điều này đảm bảo tính tương thích với chuẩn OpenTelemetry phân tán mà không làm phức tạp hóa định dạng log JSON cục bộ.

- **Một lỗi/blocker đã gặp:**
  Server `uvicorn --reload` không tự nạp lại file `.env` khi cập nhật API key mới, dẫn đến các request chạy qua web API ban đầu không hiển thị trên Langfuse cá nhân trong khi test script độc lập lại gửi được.

- **Cách tìm nguyên nhân và xử lý:**
  So sánh danh sách traces giữa terminal script và web API, nhận diện process `uvicorn` đang chạy với biến môi trường cũ từ thời điểm khởi tạo, sau đó khởi động lại server với file `.env` mới.

- **Cách hiểu luồng Metrics → Logs → Traces:**
  Metrics phát hiện "CÁI GÌ bất thường và KHI NÀO" (Latency P95 tăng vọt lúc 23:40); Logs xác định "REQUEST NÀO bị ảnh hưởng" (Tìm ra `correlation_id: req-9b19fefc` có `latency_ms: 3631`); Traces chỉ ra "TẠI SAO và BƯỚC NÀO bị lỗi" (Span `retrieval` bị trễ 2.5s).

- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  Prompt versioning giúp kiểm soát prompt như mã nguồn phần mềm, liên kết trực tiếp với trace để đánh giá chi phí token và chất lượng đầu ra. Cơ chế label (`production`, `candidate`) cho phép promote hoặc rollback tức thì khi phát hiện prompt mới làm suy giảm chất lượng mà không cần deploy lại ứng dụng.

- **Điều quan trọng nhất đã học:**
  Kỹ năng xây dựng hệ thống quan sát toàn diện (Observability) cho ứng dụng LLM/RAG kết hợp 3 trụ cột Metrics, Logs, Traces và tư duy xử lý sự cố chuẩn mực dựa trên bằng chứng dữ liệu thay vì suy đoán.

- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  Chưa triển khai OpenTelemetry Collector chuyên dụng để tự động cân bằng tải và batching trace trước khi gửi lên đám mây.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
