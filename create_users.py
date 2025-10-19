import sqlite3
import os
from werkzeug.security import generate_password_hash

# --- 1. CÁC HÀM HELPER BẮT BUỘC (LẤY TỪ app.py) ---

def get_db_connection():
    # Đảm bảo kết nối trả về Row Factory
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # PHẢI ĐẢM BẢO FILE SCHEMA TỒN TẠI VÀ CHÍNH XÁC
    if not os.path.exists('schema.sql'):
        print("LỖI: Không tìm thấy file schema.sql. KHÔNG THỂ TẠO BẢNG.")
        return

    print("Khởi tạo cơ sở dữ liệu từ schema.sql...")
    with open('schema.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = get_db_connection()
    conn.executescript(sql)
    conn.commit()
    conn.close()
    print("Khởi tạo CSDL thành công.")
# --- END HÀM HELPER ---


# --- 2. LOGIC KHỞI TẠO VÀ CHÈN DỮ LIỆU ---

# BƯỚC A: KIỂM TRA VÀ TẠO CSDL
if not os.path.exists('database.db'):
    init_db()
# Nếu file database.db tồn tại nhưng bảng chưa có, init_db() không chạy.
# Tuy nhiên, ta giả định CSDL cần được tạo lại hoàn toàn.

# BƯỚC B: BẮT ĐẦU CHÈN
conn = get_db_connection()
cursor = conn.cursor()

# Thông tin nhân viên mới
username = 'minh'
password = '123456'
role = 'giam_doc'
phong_ban = 'Phòng Kinh doanh'
ho_ten = 'Ngô Tuấn Minh'
email = 'ngotuanminh2689@gmail.cm'
chuc_vu = 'Giám Đốc'

# Hash mật khẩu
hashed_password = generate_password_hash(password)

try:
    # LƯU Ý: Nếu bạn đã xóa file database.db, lệnh INSERT này sẽ hoạt động.
    # Nếu không, hãy kiểm tra lại file schema.sql để đảm bảo không bị lỗi cú pháp.
    cursor.execute('''
        INSERT INTO users 
        (username, password, role, phong_ban, ho_ten, email, chuc_vu) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, hashed_password, role, phong_ban, ho_ten, email, chuc_vu))

    conn.commit()
    print(f"\n[THÀNH CÔNG] Đã thêm người dùng: {username} ({ho_ten})")

except sqlite3.IntegrityError as e:
    print(f"\n[LỖI] Không thể thêm người dùng {username}. Lỗi: {e}")
    print("Có lẽ Username hoặc Mã NV đã tồn tại (nếu bạn có cột ma_nv).")

except sqlite3.OperationalError as e:
    # Lỗi này chính là 'no such table: users'
    print(f"\n[LỖI CSDL] Lỗi vận hành CSDL: {e}")
    print("Cần kiểm tra lại file database.db đã được xóa/tạo lại chưa.")

finally:
    conn.close()