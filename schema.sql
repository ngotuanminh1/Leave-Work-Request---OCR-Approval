DROP TABLE IF EXISTS DuyetLog;
DROP TABLE IF EXISTS Don;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- THÔNG TIN ĐĂNG NHẬP & PHÂN QUYỀN
    username TEXT UNIQUE NOT NULL,      -- Tên đăng nhập
    password TEXT NOT NULL,             -- Mật khẩu (hash)
    role TEXT NOT NULL,                 -- Vai trò: giam_doc, quan_ly, nhan_vien
    
    -- THÔNG TIN CÁ NHÂN & CÔNG VIỆC
    ma_nv TEXT UNIQUE,                  -- Mã nhân viên
    ho_ten TEXT,                        -- Họ tên đầy đủ
    phong_ban TEXT,                     -- Phòng ban
    chuc_vu TEXT,                       -- Chức vụ hiển thị
    email TEXT                          -- Email nhân viên
);

CREATE TABLE Don (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten TEXT,
    ma_nv TEXT,
    phong_ban TEXT,
    loai_don TEXT,
    ngay_bat_dau TEXT,
    ngay_ket_thuc TEXT,
    ly_do TEXT,
    trang_thai TEXT,
    nguoi_duyet_hien_tai TEXT,
    file_goc TEXT,
    ket_qua_ocr TEXT,
    user_id INTEGER,
    ngay_gui TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE DuyetLog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    don_id INTEGER,
    user_id INTEGER,
    thoi_gian TEXT,
    phe_duyet TEXT,  -- 'duyet', 'tu_choi'
    ghi_chu TEXT,
    FOREIGN KEY(don_id) REFERENCES Don(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Thêm bảng ThongBao (Nếu chưa có)
CREATE TABLE IF NOT EXISTS ThongBao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    don_id INTEGER NOT NULL,
    noi_dung TEXT NOT NULL,
    da_doc BOOLEAN DEFAULT 0,
    thoi_gian TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);