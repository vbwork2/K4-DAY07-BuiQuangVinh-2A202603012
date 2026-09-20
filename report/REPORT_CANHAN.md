# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Quang Vinh
**Nhóm:** G-08
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần nhau, cho thấy hai đoạn văn có ý nghĩa/ngữ cảnh tương đồng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua có thể trả hàng trong vòng 15 ngày.
- Câu B: Khách hàng được phép hoàn trả sản phẩm trong thời hạn 15 ngày.
- Tại sao tương đồng: Cùng diễn đạt một quy định về thời hạn trả hàng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: TikTok xử lý tranh chấp hậu mãi.
- Câu B: Shopee quy định phí vận chuyển trả hàng.
- Tại sao khác: Khác nền tảng và khác nội dung chính sách.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng của vector, phù hợp với mức độ giống nhau về ngữ nghĩa hơn là độ lớn tuyệt đối của embedding.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450)`
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng thành `ceil(9900 / 400) = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk tốt hơn nhưng tốn thêm embedding và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

**Chiến lược chunking cá nhân sử dụng cho retrieval:** **Heading Chunking** (`HeadingRecursiveChunker`).

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex để nhận diện ranh giới câu, giữ dấu câu và gom tối đa `max_sentences_per_chunk`. Văn bản rỗng được trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Recursive chunking ưu tiên tách theo đoạn, dòng, câu và khoảng trắng. Với chiến lược cá nhân, `HeadingRecursiveChunker` tách trước theo Markdown/numbered heading, giữ heading trong từng chunk; section quá dài mới dùng `RecursiveChunker` để chia tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` embed nội dung và lưu `id`, `content`, `metadata`, vector trong memory. `search` embed query, tính similarity bằng dot product, sắp xếp giảm dần và lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Filter metadata được áp dụng trước similarity search để loại candidate không phù hợp. `delete_document` xóa các record có `metadata["doc_id"]` trùng document cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent retrieve top-k chunk, đưa `title`, `doc_id`, `source_url` và nội dung vào context. Prompt yêu cầu trả lời dựa trên context và nói rõ khi dữ liệu không đủ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================== 42 passed, in 0.06s ================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có thể trả hàng trong vòng 15 ngày. | Khách hàng được phép hoàn trả sản phẩm trong thời hạn 15 ngày. | cao | 0.920097 | Có |
| 2 | Người bán phải phản hồi yêu cầu hoàn tiền. | Seller cần phản hồi tranh chấp của khách hàng. | cao | 0.808946 | Có |
| 3 | Sản phẩm bị lỗi có thể được hoàn tiền. | Hàng hư hỏng có thể đủ điều kiện trả lại. | cao | 0.622157 | Có |
| 4 | Người mua yêu cầu hoàn tiền. | Người bán cập nhật tồn kho. | thấp | 0.574397 | Không |
| 5 | TikTok xử lý tranh chấp hậu mãi. | Shopee quy định phí vận chuyển trả hàng. | thấp | 0.104147 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 bất ngờ nhất vì score vẫn khá cao dù hai câu khác tác vụ. Điều này cho thấy embedding có thể bị ảnh hưởng bởi ngữ cảnh/chủ đề chung, nên không nên chỉ dựa vào một threshold để kết luận hai câu đồng nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược cá nhân:** **Heading/Section-aware Chunking** với `HeadingRecursiveChunker` (`chunk_size=500`). Corpus policy có các heading Markdown và section đánh số; heading mang ngữ cảnh về điều kiện, quy trình, bước xử lý, thời hạn và ngoại lệ. Với section dài, strategy dùng `RecursiveChunker` cho body rồi prepend heading vào mọi child chunk, tránh tách body khỏi tiêu đề section.

Canonical benchmark đã chạy bằng `local` embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và `heading` chunker. Metadata `platform` hiện có trên cả 8 tài liệu, Q1/Q2 dùng `platform=shopee`, Q3 giữ `audience=buyer`, Q4 dùng `platform=tiktok_shop`, và Q5 giữ `audience=seller`.

| Metric | Kết quả Heading |
|---|---:|
| Chunks | 232 |
| Gold@1 / Document@1 | 4 / 5 |
| Gold@3 / Document@3 | 4 / 5 |
| Document retrieval score | 8 / 10 |
| Evidence@1 | 1 / 5 |
| Evidence@3 | 3 / 5 |
| Evidence score | 4 / 10 |

Evidence benchmark chạy cùng `local` embedding cho tất cả strategy đạt: Fixed `0/10`, Sentence `0/10`, Recursive `1/10`, Heading `4/10`. Kết quả này cho thấy Heading giữ được evidence tốt hơn trong cấu hình local hiện tại, nhưng không dùng để so trực tiếp với kết quả Gemini của các thành viên khác nếu chưa chạy cùng backend embedding.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hoàn Tiền Ngay và Trả hàng & Hoàn tiền khác nhau thế nào? | `shopee-request-processing#1` | 0.782042 | Gold document top-1; full evidence không ở top-3 | **Incorrect** — context thiếu đủ thông tin về `vòng 6 ngày`, agent từ chối kết luận |
| 2 | Trả một phần đơn Shopee có hoàn phí ship ban đầu không? | `shopee-return-refund-policy#39` | 0.787984 | Không phải gold document; gold document không ở top-3 | **Incorrect** — retrieval không lấy được evidence về phí vận chuyển ban đầu |
| 3 | Buyer Shopee cần bằng chứng gì khi hàng lỗi/khác mô tả? | `shopee-return-evidence#9` | 0.716814 | Gold document top-1; full evidence rank 3 | **Correct** — nêu video mở kiện liên tục, cận cảnh lỗi và bằng chứng bổ sung |
| 4 | Seller TikTok phải khắc phục trong bao lâu? | `tiktok-aftersales-disputes#9` | 0.829257 | Gold document và full evidence top-1 | **Partial** — trả lời đúng `48 giờ` nhưng thiếu hành động hoàn tiền/đổi sản phẩm |
| 5 | Seller TikTok gửi trả sản phẩm trong bao lâu và làm gì? | `tiktok-seller-to-customer-returns#6` | 0.850666 | Gold document top-1; full evidence rank 3 | **Correct** — nêu `1 ngày làm việc`, đóng gói, dán nhãn và gửi bằng đơn vị có mã vận đơn |

**Bao nhiêu câu hỏi trả về gold document trong top-3?** 4 / 5. 
**Bao nhiêu câu hỏi trả về đầy đủ evidence trong top-3?** 3 / 5.

Điểm mạnh quan sát được của Heading là giữ tiêu đề/section đi cùng phần nội dung con, nên Q4 lấy được đầy đủ evidence ở top-1 và Q3/Q5 vẫn có evidence trong top-3. Hạn chế chính là số chunk tăng lên 232 và Q2 bị nhiễu bởi các điều khoản hoàn tiền/vận chuyển gần nghĩa trong tài liệu chính sách tổng quát.

Agent benchmark: Heading chunker, local embedding, `top_k=3`. Kết quả: **2/5 correct, 1/5 partial, 2/5 incorrect**. Theo rubric 2/1/0 của lab: Q1 = 1 điểm (có tài liệu liên quan nhưng thiếu evidence), Q2 = 0 điểm, Q3 = 2 điểm, Q4 = 1 điểm, Q5 = 2 điểm, tổng **6/10** cho Competition Results.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Fixed-size có thể đạt thứ hạng tài liệu tốt dù chunk kém tự nhiên hơn, còn sentence chunking giữ câu dễ đọc nhưng không đảm bảo top-1. Vì vậy cần đánh giá đồng thời document rank, evidence rank và tính mạch lạc thay vì chỉ nhìn một metric.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5 / 5            |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10          |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30          |
| Dự đoán độ tương tự (Similarity Predictions)    | 5 / 5            |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10          |
| **Tổng phần cá nhân**                           | **55 / 60**      |
