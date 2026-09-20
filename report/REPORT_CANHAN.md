# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Quang Vinh<br>
**Nhóm:** [Nhóm bổ sung]<br>
**Ngày:** 20/09/2026

## 1. Khởi động

Cosine similarity đo góc giữa hai vector thay vì độ lớn của vector. Với text embeddings, hướng của vector thường phản ánh tốt hơn mức độ gần nhau về ngữ nghĩa; vì vậy cosine phù hợp hơn Euclidean distance khi độ lớn embedding không mang ý nghĩa chính.

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`, số chunk là `ceil((10000 - 50) / (500 - 50)) = 23`. Nếu overlap tăng thành 100 thì số chunk là `ceil(9900 / 400) = 25`; ngữ cảnh ở ranh giới được giữ tốt hơn nhưng cần nhiều embedding và lưu trữ hơn.

## 2. Hướng tiếp cận của tôi

`SentenceChunker.chunk()` dùng regex để tìm ranh giới câu, giữ dấu câu và nhóm tối đa `max_sentences_per_chunk` câu. `RecursiveChunker` ưu tiên ngắt theo đoạn, dòng, câu, khoảng trắng, sau đó hard-split khi hết separator; các mảnh nhỏ liền kề được ghép lại nếu vẫn nằm trong giới hạn kích thước.

`EmbeddingStore.add_documents()` chuyển `content` của mỗi `Document` thành embedding qua `embedding_fn`, rồi lưu `id`, `content`, bản sao `metadata`, và embedding vào in-memory store. Khi search, query cũng được embed, tính dot product với các vector đã lưu, sắp xếp giảm dần theo score và lấy top-k.

`search_with_filter()` lọc các candidate theo toàn bộ key/value trong metadata trước khi similarity search, nên document ngoài phạm vi không chiếm vị trí top-k. `delete_document()` bỏ mọi record có `metadata["doc_id"]` trùng với document cần xóa.

`KnowledgeBaseAgent.answer()` retrieve top-k chunk, tạo context có `title`, `doc_id`, `source_url`, sau đó inject context và question vào grounded prompt. Prompt yêu cầu chỉ dùng context, nói rõ khi thiếu thông tin và không tự tạo facts. Hàm hiện hỗ trợ `metadata_filter` nhưng vẫn tương thích với `agent.answer("question")`.

## 3. Hoàn thiện code

Kết quả đầy đủ nằm trong `pytest_output.txt`.

```text
======================== 42 passed, 1 warning in 0.06s ========================
```

**Số lượng bài test vượt qua:** 42 / 42

## 4. Dự đoán độ tương tự

Kết quả dưới đây lấy từ `similarity_results.txt`, chạy với `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và threshold thực nghiệm 0.55. Threshold này chỉ là quy ước cho experiment, không phải ngưỡng semantic phổ quát.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua có thể trả hàng trong vòng 15 ngày. | Khách hàng được phép hoàn trả sản phẩm trong thời hạn 15 ngày. | cao | 0.920097 | Có |
| 2 | Người bán phải phản hồi yêu cầu hoàn tiền. | Seller cần phản hồi tranh chấp của khách hàng. | cao | 0.808946 | Có |
| 3 | Sản phẩm bị lỗi có thể được hoàn tiền. | Hàng hư hỏng có thể đủ điều kiện trả lại. | cao | 0.622157 | Có |
| 4 | Người mua yêu cầu hoàn tiền. | Người bán cập nhật tồn kho. | thấp | 0.574397 | Không |
| 5 | TikTok xử lý tranh chấp hậu mãi. | Shopee quy định phí vận chuyển trả hàng. | thấp | 0.104147 | Có |

Kết quả bất ngờ nhất là cặp 4: hai câu vẫn vượt threshold dù chủ thể và tác vụ khác nhau. Điều này cho thấy cùng ngữ cảnh marketplace/hoàn tiền có thể làm embedding gần nhau; vì vậy threshold đơn lẻ không đủ để khẳng định hai câu đồng nghĩa.

## 5. Kết quả truy xuất của tôi

`ket_qua_benchmark_recursive.txt` là benchmark document-level đã có trong repo, chạy với local embedding và recursive chunking. Bảng này không gọi document hit là evidence hit. `bench_evidence.py` đã được bổ sung để đánh giá nghiêm ngặt evidence/chunk-level; kết quả local mới phải được chạy lại trong môi trường có `sentence-transformers` trước khi thay thế các ghi chú evidence chưa xác định dưới đây.

| # | Query | Top-1 chunk | Score | Document-level result | Agent answer |
|---|---|---|---:|---|---|
| 1 | So sánh Hoàn Tiền Ngay và Trả hàng & Hoàn tiền | `shopee-return-shipping-fees`, không phải gold doc | 0.628361 | Gold doc không ở top-3 | Not evaluated with a generation LLM |
| 2 | Hoàn phí vận chuyển ban đầu khi trả một phần đơn | Không có candidate vì filter `platform=shopee` không có trong frontmatter | — | Gold doc không tìm thấy | Not evaluated with a generation LLM |
| 3 | Bằng chứng Shopee cho hàng lỗi/khác mô tả | `shopee-return-evidence` | 0.715370 | Gold doc rank 1; A/B unfiltered: not found, filtered: rank 1 | Not evaluated with a generation LLM |
| 4 | Hành động khắc phục TikTok trong 48 giờ | Không có candidate vì filter `platform=tiktok_shop` không có trong frontmatter | — | Gold doc không tìm thấy sau filter | Not evaluated with a generation LLM |
| 5 | Người bán TikTok gửi trả hàng cho người mua | `tiktok-aftersales-disputes`, không phải gold doc | 0.809734 | Gold doc ở rank 3 | Not evaluated with a generation LLM |

Document-level summary hiện có là Gold@1 = 1/5, Gold@3 = 2/5, document retrieval score = 3/10. Đây không phải final retrieval quality: agent generation chưa được đánh giá bằng LLM thật, và evidence-level score cần lấy từ `bench_evidence.py` với local backend.

## Tự đánh giá

| Tiêu chí | Trạng thái |
|---|---|
| Khởi động | Hoàn thành phần giải thích và tính chunking |
| Hướng tiếp cận | Hoàn thành dựa trên implementation |
| Core implementation | 42 / 42 tests passed |
| Similarity predictions | 4 / 5 dự đoán đúng theo threshold 0.55 |
| Agent generation evaluation | Chưa đánh giá với generation LLM thật |
