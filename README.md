<h1 align="center">
🚗 Xử lý Đơn xin Nghỉ phép và Đề nghị Công tác – OCR trích dữ liệu, gửi duyệt qua hệ thống.
</h1>
<div align="center">
  <img src="README/logoDaiNam.png" alt="DaiNam University Logo" width="250">
</div>
<br>
<div align="center">

[![FIT DNU](https://img.shields.io/badge/-FIT%20DNU-28a745?style=for-the-badge)](https://fitdnu.net/)
[![DAINAM UNIVERSITY](https://img.shields.io/badge/-DAINAM%20UNIVERSITY-dc3545?style=for-the-badge)](https://dainam.edu.vn/vi)

</div>


<hr>

<h2 align="center">✨ Mô tả dự án</h2>
<p align="justify">
  Dự án này là một giải pháp E-Workflow <strong>(Luồng công việc điện tử)</strong> tiên tiến <strong>nhằm số hóa và tự động hóa</strong> hoàn toàn quy trình xử lý đơn hành chính <strong>(Đơn xin nghỉ, công tác, thôi việc, thanh toán)</strong>. trong môi trường doanh nghiệp.  
  <strong>Giải quyết thách thức lớn nhất là xử lý văn bản tiếng việt</strong>, không chuẩn từ ảnh(lỗi dấu, dính chữ) bằng phương pháp lai ghép (Hybrid) giữa OCR truyền thống<strong> và Trí tuệ nhân tạo</strong> tạo sinh (LLM).
</p>

<hr>

<h2 align="center">🚀 Cấu trúc dự án</h2>
<pre>
📂 OCR/
├── 📁 .venv/                 # Môi trường ảo Python
├── 📁 static/                # TÀI NGUYÊN TĨNH VÀ UPLOAD CÔNG KHAI
│   ├── 📁 css/               # File CSS (dbadmin.css, don_detail.css, v.v.)
│   ├── 📁 uploads/           # File ảnh gốc (sao chép từ uploads/ cho web server)
│   └── 🖼️ README             # (Bạn đã có file README, có thể xóa file này)
├── 📁 templates/             # TẤT CẢ CÁC FILE HTML (Jinja2)
├── 📁 uploads/               # ẢNH ĐƠN GỐC (KHÔNG CÔNG KHAI)
├── 📜 .env                   # Cấu hình biến môi trường (API Keys, Mail)
├── 📜 app.py                 # FILE CHÍNH (Routing, Flask Logic, App Config)
├── 📜 create_users.py        # Script tạo người dùng admin/mẫu
├── 📜 database.db            # Database SQLite (chứa dữ liệu hoạt động)
├── 📜 requirements.txt       # Danh sách thư viện Python
├── 📜 schema.sql             # Khởi tạo cấu trúc bảng (users, Don, DuyetLog, ThongBao)
├── 📜 README.md              # TÀI LIỆU DỰ ÁN (Bản mô tả GitHub)
</pre>


<hr>


## 🚀 Tính Năng Chính

<p>Tải lên Đơn từ: Người dùng có thể tải lên ảnh chụp hoặc file PDF của đơn từ.

Trích xuất Dữ liệu (OCR & AI):

Sử dụng Pytesseract để trích xuất văn bản từ hình ảnh.

Tích hợp Google Gemini để làm sạch văn bản OCR và trích xuất các trường dữ liệu quan trọng (Họ tên, Mã NV, Phòng ban, Loại đơn, Ngày bắt đầu/kết thúc, Lý do) thành định dạng JSON.

Cơ chế fallback sử dụng regex để parse dữ liệu nếu AI không khả dụng hoặc thất bại.

Quy trình Duyệt đa cấp:

Hỗ trợ nhiều vai trò người dùng: nhan_vien (người nộp đơn), quan_ly (trưởng phòng), nhan_su, ke_toan, giam_doc.

Quy trình duyệt tự động chuyển cấp dựa trên loại đơn và phòng ban.

Xử lý đặc biệt cho các đơn có "lý do đặc biệt" (hiếu hỷ, thai sản) có thể được duyệt tự động.

Quản lý người dùng: Admin có thể thêm, sửa, xóa thông tin nhân viên và phân quyền.

Thông báo & Email:

Gửi thông báo real-time trong hệ thống khi trạng thái đơn thay đổi.

Gửi email thông báo phê duyệt/từ chối đơn cho người nộp đơn.

Dashboard duyệt: Cho phép người duyệt xem và xử lý các đơn đang chờ mình.

Thống kê: Cung cấp các biểu đồ và số liệu tổng quan về tình hình đơn từ trong hệ thống.

Giao diện thân thiện: Giao diện đơn giản, dễ sử dụng cho cả người nộp và người duyệt</p>