# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Quang Vinh
**Nhóm:** [Tên nhóm]
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Cosine similarity cao nghĩa là hai vector embedding có hướng gần giống nhau, thường cho thấy hai đoạn văn có nội dung/ngữ nghĩa tương tự. Tập trung vào hướng của vector hơn là độ lớn, nên phù hợp để so sánh text embedding.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể hoàn trả sản phẩm trong vòng 7 ngày.
- Câu B: Người mua được phép trả lại hàng trong thời hạn 7 ngày.
- Tại sao tương đồng: khác từ vựng nhưng gần như cùng ý nghĩa

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người mua có thể yêu cầu hoàn tiền cho đơn hàng bị lỗi.
- Câu B: Người bán phải cập nhật số lượng tồn kho của sản phẩm.
- Tại sao khác: Khác nhau về ngữ nghĩa: một câu nói về refund của buyer, câu kia nói về inventory của seller.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Vì  cosine tập trung vào hướng của vector hơn là độ lớn, nên phù hợp để so sánh text embedding. Euclid chỉ tập chung về độ lớn giữa 2 vector embedding nên chưa thể hiện được về ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* ceil((10000−50)/(500−50))=ceil(9950/450)=23
> *Đáp án:* 23

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> ceil((10000−100)/(500−100))=ceil(9900/400)=25
> *Viết 1-2 câu:* Vậy **23 chunks → 25 chunks**. Overlap lớn hơn giúp giữ context ở ranh giới giữa hai chunk, nhưng đổi lại số chunk tăng, tốn embedding/storage/retrieval hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex để xác định ranh giới câu mà không loại bỏ dấu câu, sau đó nhóm các câu liên tiếp thành từng chunk với giới hạn `max_sentences_per_chunk`. Với input rỗng, hàm trả về danh sách rỗng. Một hạn chế là các chữ viết tắt như “TS.” hoặc số thập phân có thể bị nhận diện nhầm là điểm kết thúc câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Ưu tiên chia văn bản theo các separator mang nhiều ngữ nghĩa nhất như đoạn văn và dòng mới, sau đó mới chuyển xuống câu và khoảng trắng. Nếu một đoạn vẫn vượt `chunk_size`, `_split()` tiếp tục gọi đệ quy với separator tiếp theo. Khi không còn separator, dùng hard split làm base case và sau đó ghép các mảnh nhỏ liền kề để tránh sinh quá nhiều chunk vụn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
