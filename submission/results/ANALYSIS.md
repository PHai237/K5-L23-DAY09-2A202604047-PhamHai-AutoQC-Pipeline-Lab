# Phân tích kết quả train Day 09 — raw vs clean

**Nguồn bằng chứng:** bốn file `raw_seed0.json`, `raw_seed1.json`, `clean_seed0.json`, `clean_seed1.json`, và `comparison.md|json|png` do Colab chạy `scripts/train_compare.py` rồi `scripts/summarize_results.py` sinh. **Không chỉnh sửa số liệu train.**

## 1. Thiết kế thí nghiệm

- Model/khởi tạo: `yolo26n.pt`; mỗi biến thể dùng cùng **20 epochs, batch 16, imgsz 640**, seed **0 và 1**, GPU `device=0` như trong JSON.
- `raw` = dữ liệu nguyên trạng từ `data/raw`, **224 ảnh được chuẩn bị**; `clean` = **202 ảnh** được pipeline giữ theo `manifest.json`, có nhãn đã qua kiểm và review mô phỏng.
- Tập validation: `data/gold_val` **40 ảnh**; tập test cuối: `data/test` **100 ảnh**. Không dùng test để hiệu chỉnh hai ngưỡng hay sửa nhãn.
- **Điều kiện tái lập:** `config_sha1` của bốn JSON = `78abb4ce79dc9aa9ff39772363bbe5f4ebc45191`; `manifest_sha1` của hai run clean = `add98fcd2f21e01a7c21ddb313bcde87f79735a4` (khớp bản đã train). Trọng số `.pt` không được đưa lên GitHub.

## 2. Kết quả theo seed và độ nhiễu

| Biến thể | Seed | mAP50 | mAP50–95 | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Raw | 0 | 0,7256 | 0,5144 | 0,8068 | 0,6291 |
| Raw | 1 | 0,7259 | 0,5090 | 0,7203 | 0,6689 |
| Clean | 0 | 0,7181 | 0,4944 | 0,7737 | 0,6475 |
| Clean | 1 | 0,7055 | 0,4860 | 0,8122 | 0,6231 |

| Chỉ số (trung bình ± SD mẫu; n=2) | Raw | Clean | Chênh clean − raw |
|---|---:|---:|---:|
| mAP50 | **0,72575 ± 0,00021** | 0,71180 ± 0,00891 | **−0,01395** |
| mAP50–95 | **0,51170 ± 0,00382** | 0,49020 ± 0,00594 | **−0,02150** |
| Precision | 0,76355 ± 0,06116 | **0,79295 ± 0,02722** | **+0,02940** |
| Recall | **0,64900 ± 0,02814** | 0,63530 ± 0,01725 | **−0,01370** |

Theo cặp seed, ΔmAP50 là **−0,0075** ở seed 0 và **−0,0204** ở seed 1. Chênh trung bình 0,01395 lớn hơn SD của clean (0,00891), nhưng mẫu chỉ **2 seed**: không có cơ sở khẳng định hiệu ứng thống kê hoặc rằng clean luôn tệ hơn. Precision chỉ cao hơn khi lấy trung bình; riêng seed 0 clean thấp hơn raw (0,7737 so với 0,8068). Chỉ nhận xét chính xác cho thí nghiệm này.

## 3. Những lớp nào thay đổi?

| Lớp | AP50 Raw (TB) | AP50 Clean (TB) | Δ Clean − Raw |
|---|---:|---:|---:|
| `car` | 0,73750 | 0,73170 | −0,00580 |
| `person` | 0,82205 | 0,83175 | +0,00970 |
| `truck` | 0,64845 | 0,55095 | **−0,09750** |
| `bus` | 0,69490 | 0,73270 | **+0,03780** |

`truck` giảm mạnh nhất, trong khi `bus` tăng nhiều nhất. Bộ raw có các cảnh báo nghi **nhầm car/truck/bus**, box lỏng, thiếu box; clean thay đổi cả **số ảnh** lẫn **nhãn**. Những thay đổi này *có thể* làm AP từng lớp khác nhau nhưng không đủ bằng chứng để quy kết nhân quả từ bốn kết quả train.

## 4. Hai giới hạn quan trọng của phép so sánh

1. **Rò rỉ test trong raw.** `submission/reports/01_intake.csv` có **5 lỗi `LEAK_TEST`** (các ảnh `img_0049`, `img_0101`, `img_0167`, `img_0174`, `img_0221`; cả năm đều trùng với ảnh trong `data/test/images`). Script gốc `scripts/materialize_dataset.py` cố ý sao chép toàn bộ raw làm baseline; do đó nguy cơ ảnh trùng với tập test/gold_val xuất hiện trong train raw. Không thể từ các chỉ số hiện tại định lượng mAP raw bị thổi phồng bao nhiêu. Không sửa script do giảng viên bảo vệ hoặc tự xóa ảnh khỏi raw; chỉ báo cáo giới hạn và đề nghị đánh giá lại bằng giao thức không rò rỉ trong nghiên cứu tiếp theo.
2. **Clean chưa được Release.** Pipeline ra **HOLD**, 0 ERROR nhưng **62/202 ảnh có cảnh báo chưa duyệt (30,69%)**; **80 ảnh duyệt là mô phỏng**. Bộ clean vì vậy không phải nhãn chuẩn tuyệt đối, và có **22 ảnh ít hơn raw**. Các lượt train raw có thể gặp ảnh/nhãn hỏng bị Ultralytics tự loại; số **224** trong JSON là số file ảnh được copy, chưa phải số mẫu thực sự qua bước train. Muốn biết số được Ultralytics chấp nhận phải đọc log cache/train của Colab; ZIP hiện tại không lưu log đó.

## 5. Kết luận và việc tiếp theo

**Không kết luận clean tốt hơn raw.** Trên test hiện tại mAP50 và mAP50–95 thấp hơn, dù precision trung bình tăng. Không đánh đồng kết quả Hold với thất bại rubric: mục tiêu là thực nghiệm công bằng theo cấu hình bài, nêu rõ sai lệch và hạn chế. Việc cần làm để cải thiện đánh giá: (a) tiếp tục người duyệt thật các ảnh có cảnh báo mà không thay đổi ngưỡng gate/budget để ép Release, (b) kiểm soát rò rỉ test/val khi có một protocol riêng được giảng viên cho phép, (c) nếu có điều kiện chạy thêm seed và xem log Ultralytics, nhất là các ảnh bị loại khi train raw. Không tạo thêm metric hoặc sửa JSON đã sinh.
