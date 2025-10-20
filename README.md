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

<h2 align="center">Hoạt động của hệ thống</h2>
<div align="center">
  <img src="README/sodoluong.jpg" alt="Kiến trúc hệ thống" width="100%">
</div>

<hr>

<h2 align="center">✨ Mô tả dự án</h2>
<p align="justify">
Dự án này là một giải pháp **E-Workflow (Luồng công việc điện tử)** tiên tiến nhằm số hóa và tự động hóa hoàn toàn quy trình xử lý đơn hành chính <strong>(Đơn xin nghỉ, công tác, thôi việc, thanh toán)</strong> trong môi trường doanh nghiệp.
<br><br>
Chúng tôi giải quyết thách thức lớn nhất là xử lý **văn bản tiếng Việt không chuẩn** từ ảnh (lỗi dấu, dính chữ) bằng phương pháp lai ghép (**Hybrid**) giữa OCR truyền thống **và Trí tuệ nhân tạo** tạo sinh (LLM).
</p>

<hr>

<h2 align="center">🚀 Cấu trúc dự án</h2>
<pre>
📂 OCR/
├── 📁 .venv/                 # Môi trường ảo Python
├── 📁 static/                # TÀI NGUYÊN TĨNH VÀ UPLOAD CÔNG KHAI
│   ├── 📁 css/
│   ├── 📁 uploads/
│   └── (các file hiển thị khác)
├── 📁 templates/             # TẤT CẢ CÁC FILE HTML (Jinja2)
├── 📁 uploads/               # ẢNH ĐƠN GỐC (KHÔNG CÔNG KHAI)
├── 📜 .env                   # Cấu hình biến môi trường (API Keys, Mail)
├── 📜 app.py                 # FILE CHÍNH (Routing, Flask Logic, App Config)
├── 📜 database.db            # Database SQLite (sẽ được tạo tự động)
├── 📜 requirements.txt       # Danh sách thư viện Python
├── 📜 schema.sql             # Khởi tạo cấu trúc bảng (users, Don, DuyetLog, ThongBao)
└── 📘 README.md
</pre>

<hr>


<h2 align="center">✨ Tính năng Chính</h2>

* **Tải lên Đơn từ:** Người dùng có thể dễ dàng tải lên ảnh chụp hoặc tệp PDF của các loại đơn từ khác nhau.

* **Trích xuất Dữ liệu thông minh (OCR & AI):**
    * Sử dụng **Pytesseract** để nhận diện và trích xuất văn bản từ hình ảnh/PDF.
    * Tích hợp **Google Gemini** để làm sạch dữ liệu OCR thô, sau đó phân tích và trích xuất các trường thông tin quan trọng như Họ tên, Mã nhân viên, Phòng ban, Loại đơn, Ngày bắt đầu/kết thúc, Lý do, v.v., thành định dạng JSON có cấu trúc.
    * Cơ chế **fallback (dự phòng)** thông minh sử dụng Regular Expressions (Regex) để đảm bảo việc trích xuất dữ liệu vẫn hoạt động hiệu quả ngay cả khi API AI không khả dụng hoặc trả về kết quả không mong muốn.

* **Quy trình Duyệt đa cấp linh hoạt:**
    * Hỗ trợ nhiều vai trò người dùng với các quyền hạn khác nhau: `nhan_vien` (người nộp đơn), `quan_ly` (trưởng phòng), `nhan_su`, `ke_toan`, và `giam_doc`.
    * Quy trình duyệt được tự động điều hướng và chuyển cấp dựa trên **loại đơn** và **phòng ban** của người nộp.
    * Xử lý đặc biệt cho các đơn có "lý do đặc biệt" (ví dụ: đơn xin nghỉ hiếu hỷ, thai sản) có thể được phê duyệt tự động để tối ưu hóa quy trình.

* **Quản lý người dùng tập trung:**
    * Admin có quyền thêm mới, chỉnh sửa thông tin và phân quyền cho các tài khoản nhân viên trong hệ thống.

* **Thông báo & Email tự động:**
    * Gửi thông báo **real-time** ngay trong ứng dụng khi trạng thái của đơn từ thay đổi (ví dụ: được phê duyệt, từ chối, chuyển cấp duyệt).
    * Tự động gửi email thông báo chi tiết (phê duyệt/từ chối) đến người nộp đơn, bao gồm cả lý do từ chối nếu có.

* **Dashboard Duyệt trực quan:**
    * Cung cấp giao diện dashboard riêng biệt, cho phép người duyệt dễ dàng xem, theo dõi và xử lý các đơn từ đang chờ sự phê duyệt của mình.

* **Thống kê & Báo cáo:**
    * Cung cấp các biểu đồ và số liệu thống kê tổng quan, giúp ban lãnh đạo và phòng ban liên quan nắm bắt tình hình xử lý đơn từ trong toàn hệ thống.

* **Giao diện thân thiện:**
    * Thiết kế giao diện người dùng đơn giản, trực quan, đảm bảo trải nghiệm dễ dàng và hiệu quả cho tất cả người dùng, từ người nộp đơn đến người duyệt.

    <hr>


### 💻 Công nghệ sử dụng

<div align="center>



[![Python](https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](#)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](#)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-for-the-badge&logo=sqlite&logoColor=white)](#)
[![OpenCV](https://img.shields.io/badge/OpenCV-27338E?style=for-the-badge&logo=opencv&logoColor=white)](#)
[![Tesseract OCR](https://img.shields.io/badge/Tesseract%20OCR-F38B00?style=for-the-badge)](#)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](#)
[![Flask-Mail](https://img.shields.io/badge/Flask--Mail-007ACC?style=for-the-badge)](#)
[![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](#)
[![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](#)
[![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](#)
[![VS Code](https://img.shields.io/badge/-Visual%20Studio%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](#)

</div>


<hr>


<h2 align="center">📦 Chạy và cài đặt</h2>
<p align="justify">
<strong>Chuẩn bị môi trường</strong>
</p>

<p><strong>1. Tạo môi trường ảo (Virtual Environment): </strong></p>
<pre><code>python -m venv venv
# Kích hoạt môi trường ảo:
# Trên Windows: .\venv\Scripts\activate
# Trên macOS/Linux: source venv/bin/activate</code></pre>

<p><strong>2. Cài đặt các Thư viện:</strong></p>
<pre><code>pip install -r requirements.txt</code></pre>
<p><em>(Nếu chưa có requirements.txt, bạn cần liệt kê các gói: Flask, Flask-Mail, pytesseract, opencv-python, unidecode, google-generativeai, v.v.)</em></p>


<p><strong>3. Cài đặt Tesseract OCR Engine: </strong></p>
<p><strong>Windows:</strong> Tải xuống trình cài đặt từ Tesseract-OCR GitHub. **Đảm bảo thêm đường dẫn <code>tesseract.exe</code> vào biến môi trường <code>PATH</code>.**</p>
<p><strong>Cài đặt ngôn ngữ tiếng Việt:</strong> Tìm file ngôn ngữ <code>vie.traineddata</code> và sao chép vào thư mục <code>tessdata</code> (thường là <code>C:\Program Files\Tesseract-OCR\tessdata</code>).</p>


<p><strong>4. Cấu hình Biến Môi trường (.env)</strong></p>
<p>Tạo file <code>.env</code> và điền các thông số:
<pre><code>APP_SECRET_KEY="một_chuỗi_bí_mật_mạnh_cho_flask_session"
GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
MAIL_USERNAME='email_cua_ban@gmail.com'
MAIL_PASSWORD='your_app_password' 
MAIL_DEFAULT_SENDER='email_cua_ban@gmail.com'
PORT=5000</code></pre>
<p><em>Lưu ý về <code>MAIL_PASSWORD</code>: Bạn phải sử dụng **Mật khẩu ứng dụng** (App password) cho tài khoản Gmail của mình.</em></p>


<p><strong>5. Khởi tạo Cơ sở dữ liệu & Chạy server</strong></p>
<pre><code>python app.py</code></pre>
<p><em>Ứng dụng sẽ chạy tại <code>http://127.0.0.1:5000</code> (hoặc cổng đã cấu hình trong .env).</em></p>

<hr>

<h2 align="center">📸 Kết quả chương trình</h2>
<div align="center">
  <p><strong>Tổng quan chương trình</strong></p>
  <img src="README/image1.png" alt="Ảnh Dashboard" width="100%">


<h2 align="center">🤝 Đồng đội & Giấy phép</h2>
<p>Dự án được phát triển bởi:</p>
<center>
<table>
  <thead>
    <tr>
      <th>Vai trò</th>
      <th>Giảng viên/Tên</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Giảng viên hướng dẫn</td>
      <td>ThS. Lê Trung Hiếu</td>
    </tr>
    <tr>
      <td>Giảng viên hướng dẫn</td>
      <td>KS. Nguyễn Thái Khánh</td>
    </tr>
    <tr>
      <td>Ngô Tuấn Minh</td>
      <td>1571020175</td>
    </tr>
    <tr>
      <td>Nguyễn Trung Kiên</td>
      <td>xxxxxxxx</td>
    </tr>
  </tbody>
</table>
</center>
<p align="center">© 2025 NGÔ TUẤN MINH, CNTT16-06, TRƯỜNG ĐẠI HỌC ĐẠI NAM</p>