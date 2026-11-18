# Báo cáo Day 09 — Phạm Hải, 2A202604047

## 1. Kết luận

Sau khi chạy pipeline AutoQC, tôi giữ kết quả ở trạng thái **HOLD**, chưa phát hành dataset. Trong **224 ảnh** đầu vào, bước intake loại **22 ảnh** và giữ lại **202 ảnh**. Sau ba vòng kiểm tra, sửa tự động và lượt duyệt mô phỏng **80 ảnh**, pipeline không còn lỗi bắt buộc nhưng vẫn có **62/202 ảnh** mang cảnh báo chưa được duyệt (**30,69%**). Tỷ lệ này vượt ngưỡng HOLD **10%**.

Bộ `submission/export/clean_v1/` vì vậy là **bản nháp để thử nghiệm**, không phải bản phát hành. Số liệu đối chiếu tại `08_summary.json` và `manifest.json`.

## 2. Lỗi tìm được và cách xử lý

Báo cáo `02_error_list_v1.csv` ghi nhận **455 dòng lỗi/cảnh báo**: **58 ERROR** (22 ở intake và 36 ở QC) cùng **397 WARN**. Đây là số lần phát hiện, không phải số ảnh khác nhau; lô ban đầu có 224 ảnh và còn 202 ảnh sau intake.

| Máy xử lý | Người cần xem lại |
|---|---|
| `CORRUPT_IMAGE`: 2 — ảnh hỏng | `MISSING_LABEL_FILE`: 6 — thiếu nhãn |
| `BAD_SIZE`: 3 — ảnh quá nhỏ | `EMPTY_LABEL`: 12 — xác nhận ảnh nền |
| `DUP_IMAGE_EXACT`: 8 — trùng byte | `BOX_TINY`: 6 — vật thể nhỏ |
| `DUP_IMAGE_NEAR`: 4 — gần trùng | `BOX_HUGE`: 3 — box quá lớn |
| `LEAK_TEST`: 5 — trùng tập đánh giá | `CLASS_RARE`: 4 — lớp ít đối tượng |
| `BAD_CLASS_ID`: 6 — sai ID | `POSSIBLE_MISSING`: 267 — có thể thiếu box |
| `BAD_FORMAT`: 3 — sai định dạng dòng | `POSSIBLE_LOOSE_BOX`: 58 — box lỏng |
| `BOX_ZERO`: 4 — box kích thước 0 | `POSSIBLE_FALSE_POS`: 25 — có thể thừa box |
| `BOX_OUT_OF_IMAGE`: 8 — box tràn ảnh | `POSSIBLE_WRONG_CLASS`: 22 — có thể sai lớp |
| `DUP_BOX`: 7 — box trùng | — |
| `BAD_CLASS_NAME`: 2 — sai tên lớp trong `data.yaml` | — |

Ở bước autofix, pipeline ghi **35 thao tác** trong `03_fixes.csv`: **20 lần bỏ dòng**, **8 lần cắt box**, **6 trường hợp chuyển sang gán nhãn** và **1 lần sửa bảng tên lớp**. Tôi không để máy tự tạo nhãn cho sáu ảnh thiếu file vì như vậy dễ biến ảnh chưa được gán thành ảnh nền.

Hàng đợi `05_review_queue.csv` có **147 ảnh**, ưu tiên `img_0160` (109,727 điểm), `img_0127` (44,588) và `img_0131` (29,830). Bước duyệt mô phỏng xử lý **80 ảnh**. Báo cáo vòng cuối `07_error_list_v3.csv` còn **301 cảnh báo, 0 ERROR**; trong đó **62 ảnh** vẫn chưa được duyệt.

## 3. Chọn ngưỡng calibration

Tôi chạy hai lượt sweep trên **39 ảnh calibration** rồi so precision và recall trước khi chốt cấu hình.

| Tham số | Trước → sau | Kết quả đo | Lý do chọn |
|---|---|---|---|
| `duplicates.phash_dist` | **2 → 12** | Precision/recall của `DUP_IMAGE_NEAR`: **1,00/0,50 → 1,00/0,67** | Ưu tiên tránh loại nhầm ảnh tốt, nhưng vẫn tăng khả năng phát hiện ảnh gần trùng |
| `second_opinion.conf` | **0,25 → 0,10** | `LOOSE_BOX`: **0,29/0,40 → 0,38/0,60**; `MISSING`: **0,50/1,00 → 0,40/1,00** | Muốn phát hiện thêm các ca đáng nghi để chuyển người xem, dù có thể tăng cảnh báo sai |

Có một trường hợp khiến tôi đổi lựa chọn ban đầu. Trên bộ calibration, pHash **16** đạt precision/recall **1,00/0,83** với `DUP_IMAGE_NEAR`, cao hơn ngưỡng 12. Nhưng khi xem trên raw, ngưỡng 16 lại coi `img_0011` (tennis) và `img_0008` (trượt tuyết) là gần trùng dù đó là hai cảnh khác nhau, khoảng cách pHash bằng **16**. Trong khi đó, cặp `img_0186` và `img_0061` thực sự cùng cảnh có khoảng cách **10** và vẫn được bắt ở ngưỡng 12. Vì vậy tôi chọn **12**, thay vì lấy ngưỡng có F1 cao nhất trên tập nhỏ. Bộ calib chỉ có **6 ca gần trùng**, nên kết quả ở đây chưa phản ánh hết dữ liệu raw.

## 4. Kiểm tra cửa chặn và điểm còn hạn chế

Tôi thử chạy pipeline với ngân sách duyệt bằng 0:

`python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb`

Kết quả là **Rework**, mã thoát **20**, còn **6 ERROR** và không sinh `work/exp_nb/clean_v1/manifest.json`. Khi chạy cấu hình mặc định, kết quả là **Hold**, mã thoát **10**; pipeline xuất bản nháp để tiếp tục thử nghiệm. Như vậy lỗi bắt buộc vẫn chặn việc xuất dữ liệu.

Pipeline còn hai điểm yếu: pHash có thể nhầm ảnh khác nhau hoặc bỏ sót ảnh trùng bị crop mạnh; model kiểm tra chéo vẫn bỏ sót **1/6 ca `WRONG_CLASS`** và **2/5 ca `LOOSE_BOX`** trên calib. Các cảnh báo ngữ nghĩa vì thế vẫn cần người xem.

## 5. So sánh train raw và clean trên Colab

Tôi train hai biến thể bằng `scripts/train_compare.py` với cùng **YOLO26n**, **20 epoch**, **batch 16**, kích thước ảnh **640** và hai seed **0, 1**. Cả hai dùng chung tập validation **40 ảnh** và test **100 ảnh**. Bộ raw chuẩn bị 224 ảnh; bộ clean có 202 ảnh sau pipeline.

| Chỉ số (trung bình ± độ lệch chuẩn, 2 seed) | Raw | Clean |
|---|---:|---:|
| mAP50 | **0,72575 ± 0,00021** | 0,71180 ± 0,00891 |
| mAP50–95 | **0,51170 ± 0,00382** | 0,49020 ± 0,00594 |
| Precision | 0,76355 ± 0,06116 | **0,79295 ± 0,02722** |
| Recall | **0,64900 ± 0,02814** | 0,63530 ± 0,01725 |

Chênh lệch mAP50 giữa clean và raw là **−0,01395**; ở seed 0 là **−0,0075**, còn seed 1 là **−0,0204**. Clean có precision trung bình cao hơn nhưng mAP và recall thấp hơn. Theo từng lớp, AP50 của `bus` tăng **0,0378**, `person` tăng **0,0097**, `car` giảm **0,0058**, còn `truck` giảm **0,0975**. Lớp `truck` là chỗ tôi muốn kiểm tra kỹ thêm vì mức giảm nổi bật nhất.

Tôi chưa thấy cơ sở để nói clean tốt hơn raw. Ngoài việc chỉ chạy hai seed, hai bộ train còn khác số ảnh và chất lượng nhãn. Đáng chú ý, intake phát hiện **5 ảnh `LEAK_TEST`** trong raw; việc raw chứa ảnh trùng tập test có thể khiến kết quả đánh giá cao hơn thực tế. Bộ clean cũng đang **HOLD** với 62 ảnh còn cảnh báo chưa duyệt, nên chưa thể xem là dữ liệu đã hoàn thiện. Nếu tiếp tục thí nghiệm, tôi sẽ ưu tiên kiểm tra lại các nhãn còn cảnh báo, đối chiếu số ảnh thực sự được YOLO nhận khi train và đánh giá lại trên một cách chia dữ liệu không bị trùng test.

Kết quả theo seed và biểu đồ nằm ở `submission/results/`; phân tích chi tiết trong `ANALYSIS.md`.

## 6. Quyết định cuối và cách dùng AI

Tôi giữ quyết định **HOLD** vì dù đã hết lỗi bắt buộc, tỷ lệ ảnh còn cảnh báo chưa duyệt là **30,69%**, cao hơn ngưỡng 10%. Để chuyển sang Release, cần xử lý thêm các ảnh có cảnh báo và kiểm tra lại kết quả, không chỉ thay đổi ngưỡng.

Tôi có dùng AI hỗ trợ viết bốn module theo yêu cầu đầu vào YOLO (`id cx cy w h`), quy tắc kiểm, định dạng kết quả `Issue` và giới hạn chỉ xử lý bản sao dữ liệu. Tôi đối chiếu code với docstring, chạy **79/79 unit test**, thử pipeline và kiểm các ca lỗi đã chèn trên tập calibration. Một lần tôi định dùng pHash 16 vì điểm trên calib tốt hơn; sau khi xem cặp ảnh tennis và trượt tuyết bị nhận nhầm là trùng, tôi chuyển về ngưỡng 12.

### 6(b). Bonus CVAT — kiểm tra box nhỏ

Tôi tạo **Task #22 / Job #22** trên CVAT local, import nhãn YOLO 1.1 cho năm ảnh `img_0026`, `img_0051`, `img_0069`, `img_0161` và `img_0183`, tổng cộng **33 box**. Tôi dùng bộ lọc **Width < 20 px** để tìm các box nhỏ. Theo file đo kích thước, số box khớp ở năm ảnh lần lượt là **6, 3, 2, 3, 1**, tổng **15**. Báo cáo `07_error_list_v3.csv` của pipeline có **7 cảnh báo `BOX_TINY`** trên các ảnh này, lần lượt **1, 1, 1, 3, 1**. Số lượng khác nhau vì CVAT lọc riêng chiều rộng dưới 20 px, còn pipeline cảnh báo khi **một trong hai cạnh dưới 12 px**.

Tôi kiểm tra trực tiếp frame 3 (`img_0161.jpg`): sau khi lọc, CVAT còn **3 Objects**, đúng bằng số cảnh báo `BOX_TINY` ở ảnh này. Các số đếm của bốn ảnh còn lại lấy từ file đo, chưa phải kết quả tôi kiểm tra từng frame bằng mắt.

Thuộc tính `can_review` trong CVAT có thể dùng để đánh dấu box cần xem lại. Ở pipeline, công việc tương tự được tổ chức bằng `05_review_queue.csv` dựa trên mã lỗi và mức ưu tiên; pipeline không đọc trực tiếp thuộc tính CVAT này.

Ảnh chụp điều kiện lọc và frame 3 sau khi lọc nằm trong `submission/cvat_bonus/`.
