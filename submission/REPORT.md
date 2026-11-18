# Báo cáo Day 09 — Phạm Hải, 2A202604047

## 1. Kết luận trước
**HOLD — chưa được phát hành.** Nhận **224 ảnh**, loại **22** ở intake, giữ và xuất **202 ảnh** thành **bản nháp** `submission/export/clean_v1/`. Sau QC, sửa máy và **80 ảnh được người duyệt mô phỏng** (không phải người duyệt thật), còn **0 lỗi bắt buộc**, nhưng **62/202 ảnh** còn cảnh báo chưa duyệt = **30,69%**, vượt ngưỡng Hold **10%**. Số lấy từ `08_summary.json` và manifest.

## 2. Lỗi và phân việc
`02_error_list_v1.csv`: **455 issue** = **58 ERROR** (22 intake + 36 QC) và **397 WARN**. Số sau tên mã là **dòng issue**, không phải số ảnh duy nhất; mẫu số **224 ảnh raw / 202 ảnh sau intake**.

| Máy xử lý (mã: số dòng) | Người phải xác minh (mã: số dòng) |
|---|---|
| `CORRUPT_IMAGE`: 2 — loại ảnh hỏng | `MISSING_LABEL_FILE`: 6 — gán nhãn còn thiếu |
| `BAD_SIZE`: 3 — loại ảnh quá nhỏ | `EMPTY_LABEL`: 12 — xác nhận ảnh nền |
| `DUP_IMAGE_EXACT`: 8 — loại ảnh trùng byte | `BOX_TINY`: 6 — kiểm vật nhỏ |
| `DUP_IMAGE_NEAR`: 4 — loại ảnh gần trùng | `BOX_HUGE`: 3 — kiểm box quá lớn |
| `LEAK_TEST`: 5 — loại ảnh rò rỉ | `CLASS_RARE`: 4 — kiểm phân bố lớp |
| `BAD_CLASS_ID`: 6 — bỏ dòng sai | `POSSIBLE_MISSING`: 267 — nghi bỏ sót |
| `BAD_FORMAT`: 3 — bỏ dòng hỏng | `POSSIBLE_LOOSE_BOX`: 58 — nghi box lỏng |
| `BOX_ZERO`: 4 — bỏ box rỗng | `POSSIBLE_FALSE_POS`: 25 — nghi box thừa |
| `BOX_OUT_OF_IMAGE`: 8 — cắt box | `POSSIBLE_WRONG_CLASS`: 22 — nghi nhầm lớp |
| `DUP_BOX`: 7 — bỏ box lặp | `BAD_CLASS_NAME`: 2 — máy sửa bảng `names` một lần |

`03_fixes.csv`: **35** tác vụ (20 `drop_line`, 8 `clip_box`, 6 `needs_label`, 1 `rename_classes`). `needs_label` **không** tự tạo nhãn giả: 6 lỗi này được chuyển người. `05_review_queue.csv`: **147 ảnh**, ưu tiên theo tổng trọng số lỗi/độ tin cậy model, đứng đầu `img_0160` (**109,727**), `img_0127` (**44,588**), `img_0131` (**29,830**). `06_review_log.csv`: **80/147 ảnh** được mô phỏng duyệt. `07_error_list_v3.csv`: **301 WARN, 0 ERROR**; trong đó chỉ **62 ảnh** còn WARN **chưa được duyệt** (gate đếm theo ảnh, không theo số cờ).

## 3. Calibration hai ngưỡng
**39 ảnh calib**, dùng hai sweep do script tạo (`submission/calibration/`). P/R = precision/recall, so với lỗi chèn có đáp án.

| Ngưỡng | Ban đầu → chọn | P/R trước → sau | Lý do |
|---|---|---|---|
| `duplicates.phash_dist` | **2 → 12** | `DUP_IMAGE_NEAR`: **1,00/0,50 → 1,00/0,67** | Xóa ảnh đòi **precision** cao; không chạy theo F1 đơn thuần. |
| `second_opinion.conf` | **0,25 → 0,10** | `LOOSE_BOX`: **0,29/0,40 → 0,38/0,60**; `MISSING`: **0,50/1,00 → 0,40/1,00** | Cảnh báo chỉ gợi ý người xem: ưu tiên **recall** box lỏng, chấp nhận thêm FP. |

**Calib đánh lừa:** pHash **16** cho P/R `DUP_IMAGE_NEAR` **1,00/0,83** trên calib, nhưng raw `img_0011` (**tennis**) và `img_0008` (**trượt tuyết**) lại bị nhầm là gần trùng (distance **16**), dù **khác ảnh**. Trái lại `img_0186` và `img_0061` thật sự là cùng cảnh (distance **10**), được bắt ở ngưỡng **12**. Vì calib chỉ có **6** ca gần trùng, không có `LEAK_TEST` và phân bố khác raw, phải thận trọng khi suy rộng.

## 4. Cửa chặn và điểm mù
**Thử gate âm tính:** `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` → **Rework**, mã thoát **20**, còn **6 ERROR**, **không xuất** `work/exp_nb/clean_v1/manifest.json`. Chạy mặc định → **Hold**, mã thoát **10**, có export **nháp**, không Release.

**Điểm mù:** (1) pHash có thể nhầm hai ảnh khác nhau hoặc bỏ sót cặp trùng bị crop mạnh (minh chứng tennis/trượt tuyết ở trên). (2) Model lớn không phải nhãn chuẩn: ở calib ngưỡng chọn vẫn bỏ sót **1/6 WRONG_CLASS**, **2/5 LOOSE_BOX**; nếu model và nhãn cùng sai, cảnh báo có thể không xuất hiện. Vì vậy máy kiểm quy tắc, **người kiểm ý nghĩa**.

## 5. Train raw vs clean (Colab, 2 seed)
Đã train thật bằng `scripts/train_compare.py`: **YOLO26n**, **20 epoch**, **batch 16**, **imgsz 640**, seed **0 và 1** cho mỗi biến thể; chung **val 40 / test 100 ảnh**. Raw chuẩn bị **224 ảnh**, clean **202 ảnh**. JSON gốc và `comparison.*` ở `submission/results/` (không sửa bằng tay).

| Metric (TB ± SD, 2 seed) | Raw | Clean |
|---|---:|---:|
| mAP50 | **0,72575 ± 0,00021** | 0,71180 ± 0,00891 |
| mAP50–95 | **0,51170 ± 0,00382** | 0,49020 ± 0,00594 |
| Precision | 0,76355 ± 0,06116 | **0,79295 ± 0,02722** |
| Recall | **0,64900 ± 0,02814** | 0,63530 ± 0,01725 |

ΔmAP50 (clean − raw) = **−0,01395**, âm ở cả seed 0 (−0,0075) và seed 1 (−0,0204); clean có độ lệch seed lớn hơn raw. Với **chỉ 2 seed**, chưa đủ kết luận khái quát; precision chỉ tăng về trung bình. AP50 `bus` +0,0378, `person` +0,0097, `truck` −0,0975, `car` −0,0058. Nguyên nhân *có thể* gồm thay đổi số ảnh, phân bố lớp và box/nhãn còn lỗi. Đặc biệt **5 ảnh raw rò rỉ sang test** (`LEAK_TEST`) có thể làm mAP baseline cao giả; chưa định lượng được mức ảnh hưởng. Clean vẫn là **bản nháp HOLD** (62/202 cảnh báo chưa duyệt, 80 lượt duyệt mô phỏng), không phải dữ liệu chuẩn. **Không kết luận clean tốt hơn raw.** Xem phân tích và giới hạn: `submission/results/ANALYSIS.md`.

## 6. Quyết định và dùng AI
**HOLD** cho đến khi còn **0 ERROR** và tỷ lệ ảnh cảnh báo chưa duyệt **< 10%**; phải có kế hoạch duyệt bổ sung hợp lệ, **không** tăng ngân sách 80 hoặc đổi gate để ép Release.

**AI:** (1) *Prompt*: viết bốn module kiểm YOLO `id cx cy w h`, nhận `Dataset/cfg`, trả `Issue`/log fix/verdict theo docstring/test, **không sửa** raw/tests/file đã ghim; giải thích code để người nộp hiểu. (2) *Kiểm*: đọc 4 module, chạy **79/79 pytest**, hai sweep, pipeline thật 224 ảnh, gate âm tính, đối chiếu cặp raw. (3) *Sai và sửa*: AI ban đầu thiên về pHash **16** vì F1 calib cao; kiểm ảnh phát hiện tennis/trượt tuyết bị coi trùng, hạ chọn về **12**. Người nộp tự đọc và giải thích được code trước khi nộp.
