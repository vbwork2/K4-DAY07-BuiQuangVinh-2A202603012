# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Nhóm bổ sung]<br>
**Thành viên:** [Nhóm bổ sung]<br>
**Ngày:** 20/09/2026

## 1. Lựa chọn tài liệu

### Chủ đề và lý do chọn

**Chủ đề:** Chính sách trả hàng, hoàn tiền và tranh chấp hậu mãi trên các sàn thương mại điện tử.

Corpus gồm chính sách công khai từ Shopee và TikTok Shop. Chủ đề có các quy tắc thời hạn, điều kiện, bằng chứng và đối tượng buyer/seller rõ ràng, nên phù hợp để so sánh chunking, metadata filtering và grounded retrieval.

### Danh sách tài liệu

Character count là độ dài thực tế của toàn bộ file Markdown, bao gồm frontmatter.

| # | Tên tài liệu | Nguồn | Ngày lấy / phiên bản | Số ký tự | Metadata chính |
|---|---|---|---|---:|---|
| 1 | Quy trình Shopee xử lý yêu cầu trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/190242 | 2026-09-20 / not-stated | 8693 | audience=both; category=return-process; language=vi |
| 2 | Chuẩn bị bằng chứng khi yêu cầu trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/79467 | 2026-09-20 / not-stated | 3865 | audience=buyer; category=return-evidence; language=vi |
| 3 | Chính sách trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / effective-2026-03-11 | 20130 | audience=both; category=return-refund; language=vi |
| 4 | Phương thức gửi hàng hoàn trả và phí hoàn trả Shopee | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / not-stated | 6369 | audience=buyer; category=return-shipping; language=vi |
| 5 | Nâng cấp tranh chấp hậu mãi trên TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=101756645132049 | 2026-09-20 / 2025-06-18 | 7740 | audience=seller; category=aftersales-dispute; language=vi |
| 6 | Trả hàng do đổi ý trên TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=6988871880738576 | 2026-09-20 / 2026-08-21 | 9755 | audience=buyer; category=change-of-mind; language=vi |
| 7 | Chính sách trả hàng và hoàn tiền TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=1766935302801169 | 2026-09-20 / 2026-08-21 | 20888 | audience=both; category=return-refund; language=vi |
| 8 | Người bán gửi trả sản phẩm cho người mua trên TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=4041059496167184 | 2026-09-20 / 2026-08-20 | 5915 | audience=seller; category=seller-return; language=vi |

Các nguồn được `sources.csv` ghi là public-source và frontmatter của mọi document có `source_url`, `retrieved_at`, `document_version`.

### Cấu trúc metadata

| Trường | Kiểu | Lợi ích retrieval |
|---|---|---|
| doc_id | string | Nhận diện nguồn gốc của mọi chunk, hỗ trợ delete và gold-rank. |
| title | string | Hiển thị context dễ kiểm tra. |
| source_url | URL string | Truy vết nguồn chính sách. |
| retrieved_at | ISO date string | Ghi nhận thời điểm lấy dữ liệu. |
| document_version | string | Phân biệt phiên bản/hiệu lực chính sách. |
| audience | enum | Prefilter buyer, seller hoặc both. |
| category | string | Phân biệt return, shipping, evidence và dispute. |
| language | string | Cho phép giới hạn ngôn ngữ khi corpus mở rộng. |

## 2. Thiết kế chiến lược

### Phân tích baseline

Các số liệu dưới đây lấy từ local run trong `ket_qua_benchmark_recursive.txt` với `chunk_size=500`.

| Tài liệu | Strategy | Count | Avg length |
|---|---|---:|---:|
| shopee-return-evidence | fixed_size | 8 | 477.38 |
| shopee-return-evidence | by_sentences | 12 | 286.08 |
| shopee-return-evidence | recursive | 9 | 383.00 |
| shopee-return-refund-policy | fixed_size | 44 | 494.68 |
| shopee-return-refund-policy | by_sentences | 43 | 453.44 |
| shopee-return-refund-policy | recursive | 54 | 360.98 |
| tiktok-aftersales-disputes | fixed_size | 17 | 474.53 |
| tiktok-aftersales-disputes | by_sentences | 13 | 555.69 |
| tiktok-aftersales-disputes | recursive | 17 | 425.53 |

`HeadingRecursiveChunker` đã được thêm như một strategy section-aware: heading Markdown hoặc section đánh số được đưa vào mọi child chunk của section dài. Mapping giữa strategy và từng thành viên chưa có dữ liệu, nên không tự gán tên hoặc điểm cho thành viên.

## 3. Câu hỏi đánh giá

| # | Query | Gold answer (tóm tắt) | Gold document / evidence |
|---|---|---|---|
| 1 | Hoàn Tiền Ngay và Trả hàng & Hoàn tiền khác nhau thế nào? | Hoàn Tiền Ngay không cần trả hàng; trả hàng cần gửi về trong 6 ngày. | shopee-request-processing; “Hoàn Tiền Ngay”, “vòng 6 ngày” |
| 2 | Trả một phần đơn Shopee có hoàn phí ship ban đầu không? | Không hoàn phí ship ban đầu. | shopee-return-shipping-fees; “phí vận chuyển ban đầu”, “không được hoàn lại” |
| 3 | Buyer Shopee cần bằng chứng gì khi hàng lỗi/khác mô tả? | Video mở kiện liên tục, rõ tình trạng hàng và vận đơn. | shopee-return-evidence; “video mở kiện hàng”, “liên tục” |
| 4 | Seller TikTok phải khắc phục trong bao lâu? | Trong 48 giờ; ví dụ hoàn tiền hoặc đổi sản phẩm. | tiktok-aftersales-disputes; “48 giờ”, “hoàn tiền cho khách hàng hoặc đổi sản phẩm” |
| 5 | Seller TikTok gửi trả sản phẩm trong bao lâu và làm gì? | Trong 1 ngày làm việc, đóng gói/gắn nhãn/gửi có mã vận đơn. | tiktok-seller-to-customer-returns; “1 ngày làm việc”, “mã vận đơn” |

### Metadata filter analysis

Kết quả local document-level hiện có cho Q3 cho thấy filter `{"audience": "buyer"}` cải thiện gold document từ **not found** ở unfiltered thành **rank 1** ở filtered. Đây là bằng chứng A/B về việc audience filter loại bớt semantic overlap từ tài liệu TikTok.

Tuy nhiên, Q2 và Q4 hiện dùng filter `platform` trong `bench.py`, còn frontmatter corpus không có trường `platform`; filtered search trả về rỗng. Đây là một failure configuration có thể kiểm chứng, không phải kết luận rằng metadata filtering luôn gây hại. Nếu corpus được mở rộng, metadata `platform` kết hợp `audience` và `category` có thể tách policy Shopee/TikTok tốt hơn, nhưng corpus hiện tại không được sửa tự động.

### Failure case và chất lượng dữ liệu

`ket_qua_benchmark_recursive.txt` cho Q5 đưa `tiktok-aftersales-disputes` lên top-1 (0.809734), còn gold document `tiktok-seller-to-customer-returns` ở rank 3 (0.743054). Lý do hợp lý là hai tài liệu đều nói về seller, tranh chấp và hành động sau bán hàng; `audience=seller` chưa đủ phân biệt mục đích gửi trả cụ thể.

`data_quality_notes.txt` cũng ghi nhận UI/navigation noise trong các file TikTok (ví dụ Thai/Indonesian navigation text, table of contents, feedback/footer). Những token này có thể làm giảm precision và nên được làm sạch trong một bước quản trị dữ liệu riêng, không thay đổi source hiện tại.

## 4. Phần cần nhóm xác nhận

- [Nhóm bổ sung] tên nhóm và danh sách thành viên.
- [Nhóm bổ sung] mapping strategy thực tế của từng thành viên và so sánh giữa các thành viên.
- [Nhóm bổ sung] insight sau demo và self-assessment.
- Evidence-level strategy table chỉ được điền từ `benchmark_evidence_all.txt` sau local run hoàn tất; không dùng mock score làm kết quả semantic của nhóm.
