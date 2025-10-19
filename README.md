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


### 🚀 Hướng Dẫn Cài Đặt và Chạy

<h2 align="center">📦 Chạy và cài đặt</h2>
<p align="justify">
  <strong>Chuẩn bị môi trường</strong><br>

  <strong>1. Tạo môi trường ảo (Virtual Environment): </strong><br>
 
  <code>python -m venv venv
        # Kích hoạt môi trường ảo:
        # Trên Windows: .\venv\Scripts\activate
        # Trên macOS/Linux: source venv/bin/activate</code><br><br>
  
  <strong>2. Lệnh cài thư viện:</strong><br>
  - (Tùy chọn) Tạo môi trường ảo (nên dùng <code>pip install -r requirements.txt</code>):<br>
  <p><code># Nếu chưa có requirements.txt, bạn có thể tạo thủ công bằng cách liệt kê các gói sau:</code></p>
  <code># Flask
        # python-dotenv
        # Flask-Mail
        # Werkzeug
        # opencv-python
        # pytesseract
        # unidecode
        # google-generativeai</code><br><br>

  <strong>4. Cài đặt Tesseract OCR Engine: </strong><br>
  <p><br>Windows: </br><strong> - tải xuống trình cài đặt từ Tesseract-OCR GitHub. Đảm bảo thêm đường dẫn<code>tesseract.exe </code>vào biến môi trường<code> PATH.</code></p></strong>
  <p><br>Cài đặt ngôn ngữ tiếng Việt:</br>
  <strong><br>-Tìm file ngôn ngữ <code>vie.traineddate</code>(có thể tải từ GitHub của Tesseract hoặc cài đặt qua gói ngôn ngữ Tesseract).<p><br></strong>
  <strong><p>- Sao chép<code>vie.traineddata</code> vào thư mục <code>tessdata</code> của Tesseract (thường là) <code>C:\Program Files\Tesseract-OCR\tessdata</code></p><br><br></strong>

  - <strong>4. Cấu hình Biến Môi trường (.env)</strong><br>
  <code>APP_SECRET_KEY="một_chuỗi_bí_mật_mạnh       _cho_flask_session"
        GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY" # Lấy từ Google AI Studio
        # Hoặc nếu dùng OpenAI (chỉ để fallback trong code, nên dùng Gemini nếu đã cấu hình):
        # OPENAI_API_KEY="YOUR_OPENAI_API_KEY" 

        # Cấu hình email (Gmail SMTP)
        MAIL_SERVER='smtp.gmail.com'
        MAIL_PORT=587
        MAIL_USE_TLS=True
        MAIL_USERNAME='email_cua_ban@gmail.com' # Email dùng để gửi thông báo
        MAIL_PASSWORD='your_app_password' # Tạo "App password" cho tài khoản Gmail của bạn
        MAIL_DEFAULT_SENDER='email_cua_ban@gmail.com'

        PORT=5000 # Cổng chạy ứng dụng (mặc định 5000)</code>
  <p><em>Lưu ý về <code>MAIL_PASSWORD</code> Bạn không nên sử dụng mật khẩu Gmail thông thường. Thay vào đó, hãy tạo một "App password" cho tài khoản Gmail của mình. Hướng dẫn: Tạo và sử dụng Mật khẩu ứng dụng.</em></p>
</p>

 - <strong>Chạy server:</strong><br>
  <code>node server.js</code>
  <p><em>Lưu ý: Đảm bảo đã cấu hình đúng file <code>serviceAccountKey.json</code> trước khi chạy server.</em></p>
</p>


<hr>

<h2 align="center">🧮 Bảng mạch</h2>
<p align="center">
  ⛓️‍💥 <strong>Hướng dẫn cắm dây:</strong>
</p>

<hr>