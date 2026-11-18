# Bonus CVAT — Day 09

Tôi tạo Task #22 / Job #22 trong CVAT local để kiểm tra box nhỏ của 5 ảnh: `img_0026`, `img_0051`, `img_0069`, `img_0161`, `img_0183`. Tổng số box đã import là 33.

Tôi lọc theo điều kiện **Width < 20 px**. Theo dữ liệu nhãn đã chuẩn bị, năm ảnh có lần lượt **6, 3, 2, 3, 1** box khớp bộ lọc, tổng **15**. Trong báo cáo pipeline `submission/reports/07_error_list_v3.csv`, số cảnh báo **`BOX_TINY`** tương ứng là **1, 1, 1, 3, 1**, tổng **7**. Hai phép kiểm khác nhau: CVAT xét chiều rộng dưới 20 px, pipeline xét cạnh ngắn dưới 12 px.

Tôi kiểm tra trên CVAT ở **frame 3 (`img_0161.jpg`)**: sau khi bật bộ lọc còn **3 Objects**, khớp với ba cảnh báo `BOX_TINY` của ảnh này. Các số đếm bốn ảnh còn lại lấy từ dữ liệu nhãn, không phải từ việc duyệt từng frame trên giao diện.

Minh chứng:

- `filter_width_lt20.png`: điều kiện lọc Width < 20.
- `img_0161_filtered_3objects.png`: frame 3 sau khi lọc, danh sách còn 3 Objects.

Thuộc tính `can_review` của CVAT có thể đánh dấu box cần xem lại. Pipeline Day 09 dùng `05_review_queue.csv` để sắp xếp ảnh cần duyệt, không đọc thuộc tính này từ CVAT.
