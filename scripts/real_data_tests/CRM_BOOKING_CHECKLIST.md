# Checklist CRM / Booking — KinderHealth

Chưa cấu hình và chưa kết nối CRM. Đây là danh sách cần xác nhận với khách hàng, không phải dữ liệu thực tế hoặc schema đã triển khai.

1. Lead được lưu ở đâu? Ai quản lý và ai có quyền cấp quyền đọc?
2. Booking/lịch hẹn được lưu ở đâu? Có ID lịch hẹn ổn định không?
3. Có CRM không? Tên hệ thống, đơn vị vận hành?
4. Có API không? Tài liệu, cơ chế xác thực, quyền chỉ đọc, giới hạn gọi?
5. Có database không? Có thể cung cấp view chỉ đọc hoặc bản export được duyệt không?
6. Nếu Google Sheet: Sheet ID, tab và tên cột nào? Ai cấp quyền đọc?
7. Có trường nào nối Lead với Campaign? Quy tắc attribution và cửa sổ thời gian là gì?
8. Có Meta Lead ID / UTM / gclid / phone / email không? Trường nào được phép sử dụng làm định danh và chống trùng?
9. Trạng thái hiện tại ánh xạ thế nào sang `NEW`, `CONTACTED`, `BOOKED`, `SHOW_UP`, `WON`, `LOST`? Ai xác nhận chuyển trạng thái? Có lịch sử thay đổi không?
10. Có revenue/payment không? Doanh thu ghi nhận khi nào, tiền tệ nào, xử lý hoàn/hủy ra sao?

## Schema đề xuất cho giai đoạn sau

| Trường | Ý nghĩa cần xác nhận |
|---|---|
| lead_id | ID nội bộ ổn định |
| external_lead_id | ID tại hệ thống nguồn |
| source | Hệ thống cung cấp dữ liệu |
| channel | Kênh thu hút lead |
| campaign_id | ID chiến dịch, có thể trống nếu chưa xác định |
| campaign_name | Tên chiến dịch tại nguồn |
| utm_source | UTM nguồn |
| utm_medium | UTM phương tiện |
| utm_campaign | UTM chiến dịch |
| phone_hash hoặc identifier phù hợp | Định danh đã thống nhất cách chuẩn hóa/bảo vệ; không mặc định lưu số điện thoại thô |
| created_at | Thời điểm tạo, xác định múi giờ |
| status | Trạng thái theo mapping được khách hàng duyệt |
| appointment_at | Thời điểm hẹn; để trống nếu chưa đặt lịch |
| show_up | Đã đến khám hay chưa; cho phép chưa biết |
| customer | Định danh hoặc trạng thái khách hàng, cần thống nhất nghĩa |
| revenue | Doanh thu thực được xác nhận; chưa biết không đồng nghĩa bằng 0 |

Trước khi tích hợp: xác nhận định nghĩa Lead, Booking, Show-up, Customer, Revenue; quy tắc trùng khách, nhiều lịch hẹn, nhiều lần thanh toán và attribution. Không tạo Appointment/Revenue giả. Chưa có thao tác ghi dữ liệu hoặc thay đổi database trong task này.
