# CVAT Bonus — Day 09, Task #22 / Job #22

Nguồn: CVAT local, dữ liệu Day 09, 5 ảnh đã chọn từ `submission/reports/07_error_list_v3.csv`.

## Ảnh và bằng chứng

- `filter_width_lt20.png`: ảnh chụp màn hình mới do học viên cung cấp; điều kiện lọc **Width < 20**.
- `img_0161_filtered_3objects.png`: ảnh chụp CVAT Job #22, frame 3 (`img_0161.jpg`) sau lọc, panel **Items: 3**.
- `vin_er_frame3/01-original.png`: ảnh frame 3 xuất từ Vin-ER, không chứa box overlay.
- `vin_er_frame3/02-annotated.png`: ảnh có overlay theo nhãn đã Save. Ảnh overlay có thể vẽ cả các shape bị CVAT filter ẩn.
- `vin_er_frame3/03-annotations.json`: JSON 4 box đã Save từ API Job 22, xuất *read-only*.
- `vin_er_frame3/04-qc.md`: báo cáo Vin-ER chỉ kiểm hình học; không phải nhãn chuẩn hay xác nhận độ đầy đủ.
- `vin_er_frame3/README.txt`: mô tả xuất từ công cụ Vin-ER.
- `frame3_widths.csv`: các chiều rộng/cao pixel tính trực tiếp từ JSON ở trên, không chỉnh sửa dữ liệu gốc.

## Kiểm tra chéo frame 3

| Shape ID | Class | Width (px) | Height (px) | Width < 20 | BOX_TINY (cạnh ngắn < 12) |
|---|---|---:|---:|---|---|
| 3844 | person | 31.22 | 113.78 | Không | Không |
| 3845 | person | 10.26 | 32.27 | Có | Có |
| 3846 | person | 11.40 | 43.83 | Có | Có |
| 3847 | person | 11.86 | 43.64 | Có | Có |

Kết quả: 4 box đã Save, 3 box khớp Width < 20; CVAT hiển thị 3 object sau lọc. Không sửa nhãn, không dùng Vin-ER để xác nhận nhãn đúng ngữ nghĩa. Các ảnh và annotation từ dataset lab COCO hiện đã nằm trong repo nguồn; không có dữ liệu cá nhân mới.

Báo cáo chính: `submission/REPORT.md` §6(b). Lưu ý `width < 20` khác `BOX_TINY` (`min(width, height) < 12`).
