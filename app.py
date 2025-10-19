from dotenv import load_dotenv
load_dotenv() 

# app.py
import os
import json
import sqlite3
import re
from datetime import datetime
from functools import wraps
from unidecode import unidecode
from flask_mail import Mail, Message

from flask import (
    Flask, request, render_template, redirect, url_for,
    flash, session, send_from_directory
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash 

import cv2
import numpy as np
import pytesseract


try:
    from google import genai
    from google.genai.errors import APIError
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = os.getenv("OPENAI_API_KEY") # Fallback to check OpenAI key (đề phòng bạn chưa đổi tên)

    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_MODEL = "gemini-2.5-flash" # Model hiệu quả cho tác vụ này
    else:
        client = None
        print("Warning: GEMINI_API_KEY not set — Gemini features disabled.")
        
except ImportError:
    client = None
    print("Warning: Google GenAI SDK not found (pip install google-genai) — Gemini features disabled.")
except Exception as e:
    client = None
    print(f"Error initializing Gemini client: {e} — Gemini features disabled.")

# --- Config ứng dụng ---
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "change_this_in_prod")

UPLOAD_FOLDER = 'uploads'
STATIC_UPLOAD_FOLDER = 'static/uploads'
for folder in [UPLOAD_FOLDER, STATIC_UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB limit (tùy chỉnh)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ngotuanminh2689@gmail.com'
app.config['MAIL_PASSWORD'] = 'owst focf foxk aiva' 
app.config['MAIL_DEFAULT_SENDER'] = 'ngotuanminh2689@gmail.com'

mail = Mail(app)

# --- Helper: DB ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # expects schema.sql present in same folder
    with open('schema.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = get_db_connection()
    conn.executescript(sql)
    conn.commit()
    conn.close()


# --- Xử lý ảnh / OCR ---
def preprocess_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    # resize if too large for speed (optional)
    h, w = img.shape[:2]
    max_dim = 1600
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 15
    )
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpen = cv2.filter2D(thresh, -1, kernel)
    return sharpen


def fix_common_ocr_errors(text):
    corrections = {
        'Ng$Ễn': 'Nguyễn',
        'Anb': 'Anh',
        'đa nảy': 'đây',
        'tãi': 'tôi',
        'nghl': 'nghỉ',
        'Tỗg thởi gian nghL': 'Tổng thời gian nghỉ',
        '17/82025': '17/8/2025',
        'Hiếuhr': 'Hiếu',
        'lỹdo': 'lý do',
        'Hat phúc': 'Hạnh phúc',
        'Quẻn lý': 'Quản lý',
        'đế': 'đến',
        'Kính mong Banlânhđạo': 'Kính mong Ban lãnh đạo',
        'đểukiện': 'điều kiện',
        'tổpg': 'tổng',
        'nghL': 'nghỉ',
        'Đậc': 'độc',
        'Kinh': 'Kính',
        'pbp': 'phép',
        'pbòng': 'phòng',
        'chi': 'chú',
        'Iõ': 'họ',
        'đẻukiện': 'điều kiện',
        'tửvảo': 'trừ vào',
        'thăng': 'tháng',
        'họ tê': 'họ tên',
        'tổng ! hợp': 'tổng hợp',
        'hảnh': 'hành',
        'NgrỄn': 'Nguyễn',
        'Hnong': 'Hương',
        'Đon V?': 'Đơn vị',
        'Pbòng ': 'hành',
        'thảnh ': 'thành',
        # --- BỔ SUNG LỖI TỪ ĐƠN MẪU ---
        'Kínhgửi': 'Kính gửi',
        'phác': 'phúc',
        'Hanh phác': 'Hạnh phúc',
        'linh dao': 'lãnh đạo',
        'phing': 'phòng',
        'ké toán': 'kế toán',
        'ting bop': 'tổng hợp',
        'Tit': 'Tú',           
        'viét don': 'viết đơn',
        'Téng thời gian nghi': 'Tổng thời gian nghỉ',
        'Hiéu hy': 'Hiếu hỷ',
        'chan thinh căm on': 'chân thành cảm ơn',
        # --- END BỔ SUNG ---
    }
    for w, r in corrections.items():
        text = text.replace(w, r)
    return text


def clean_text_with_gemini(ocr_text: str) -> str:
    """
    Dùng Gemini để sửa lỗi chính tả/NGẮT CÂU trong văn bản OCR tiếng Việt.
    Thay thế cho clean_text_with_openai.
    """
    if not client:
        raise RuntimeError("Gemini client not configured")

    prompt = (
        "Bạn là trợ lý xử lý văn bản OCR tiếng Việt. "
        "Nhiệm vụ: sửa lỗi chính tả, dấu, ngắt câu, từ bị dính; "
        "không thêm nội dung, chỉ chỉnh sửa để văn bản đọc tự nhiên hơn. "
        "Trả về duy nhất văn bản đã sửa (không giải thích, không danh sách).\n\n"
        "Văn bản OCR:\n"
        f"{ocr_text}\n\n"
        "Hãy trả về văn bản đã chỉnh sửa."
    )
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config={"temperature": 0.0}
        )
        # Sử dụng text thay vì content
        return response.text.strip()
    except APIError as e:
        raise RuntimeError(f"Gemini API Error: {e}")
    except Exception as e:
        raise RuntimeError(f"Gemini Clean Error: {e}")


def parse_with_gemini(ocr_text: str) -> dict:
    """
    Yêu cầu Gemini trích xuất các trường thành JSON.
    Thay thế cho parse_with_openai.
    """
    if not client:
        raise RuntimeError("Gemini client not configured")

    prompt = (
        "Bạn là trình trích xuất dữ liệu từ đơn xin nghỉ bằng tiếng Việt. "
        "Hãy trả về một JSON hợp lệ (chỉ JSON) với các trường sau: "
        "ho_ten, ma_nv, phong_ban, loai_don, ngay_bat_dau, ngay_ket_thuc, ly_do. "
        "Nếu không tìm thấy giá trị nào, gán null cho trường đó.\n\n"
        "Văn bản:\n"
        f"{ocr_text}\n\n"
        "Chỉ trả về JSON."
    )
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config={
                "temperature": 0.0,
                # Yêu cầu đầu ra JSON (chỉ dùng nếu model hỗ trợ JSON Mode)
                "response_mime_type": "application/json" 
            }
        )
        
        # Nếu model không hỗ trợ JSON Mode, bạn phải trích xuất JSON thủ công:
        json_text = response.text.strip()
        first = json_text.find('{')
        last = json_text.rfind('}')
        if first != -1 and last != -1:
            json_text = json_text[first:last + 1]
            
        data = json.loads(json_text)
        
        # normalize keys: ensure expected keys present
        keys = ['ho_ten', 'ma_nv', 'phong_ban', 'loai_don', 'ngay_bat_dau', 'ngay_ket_thuc', 'ly_do']
        out = {k: (data.get(k) if k in data else None) for k in keys}
        return out
        
    except APIError as e:
        raise RuntimeError(f"Gemini API Error: {e}")
    except Exception as e:
        raise RuntimeError(f"Gemini Parse Error: {e}")


def extract_text(image_path, use_gemini=True):
    """
    Trích xuất văn bản dùng Pytesseract.
    Trả về (cleaned_text, parsed_data_or_None)
    """
    proc = preprocess_image(image_path)
    if proc is None:
        return "", None

    text = ""
    parsed = None
    
    # --- LOGIC TESSERACT OCR ---
    try:
        lang_config = 'vie+eng' 
        text = pytesseract.image_to_string(proc, lang=lang_config)
    except Exception as e:
        print(f"Lỗi Tesseract OCR: {e}")
        text = "Lỗi khi trích xuất văn bản bằng Tesseract."

    # Áp dụng các sửa lỗi OCR chung
    text = fix_common_ocr_errors(text)

    # Thử GEMINI clean + parse nếu có thể
    if use_gemini and client: # Kiểm tra client đã được khởi tạo
        try:
            # 1. CLEAN
            cleaned = clean_text_with_gemini(text)
            
            # 2. PARSE STRUCTURED
            try:
                parsed = parse_with_gemini(cleaned)
            except Exception as parse_e:
                print("Gemini parse failed:", parse_e)
                parsed = None
                
            text = cleaned
            
        except Exception as e:
            # Log error, fallback to OCR-only text
            print("Gemini error (clean/parse):", e)

    # Nếu không dùng Gemini hoặc Gemini thất bại, trả về văn bản đã qua fix_common_ocr_errors
    return text, parsed

def send_approval_email(recipient_email, don_id, don_type, trang_thai, ghi_chu=None):
    # Xác định tiêu đề và nội dung email
    if trang_thai == 'duyet':
        subject = f"[THÔNG BÁO] Đơn {don_type} (ID: {don_id}) ĐÃ ĐƯỢC PHÊ DUYỆT"
        body = f"""
        Kính gửi Anh/Chị,
        
        Đơn {don_type} số ID: {don_id} của Anh/Chị đã được phê duyệt.
        
        Vui lòng truy cập hệ thống để xem chi tiết: {url_for('don_details', don_id=don_id, _external=True)}
        
        Trân trọng,
        Hệ thống Tự động
        """
    else: # tu_choi
        subject = f"[CẢNH BÁO] Đơn {don_type} (ID: {don_id}) ĐÃ BỊ TỪ CHỐI"
        body = f"""
        Kính gửi Anh/Chị,
        
        Rất tiếc, Đơn {don_type} số ID: {don_id} của Anh/Chị đã bị TỪ CHỐI.
        Lý do từ chối: {ghi_chu or 'Không có ghi chú chi tiết.'}
        
        Vui lòng truy cập hệ thống để xem chi tiết: {url_for('don_details', don_id=don_id, _external=True)}

        Trân trọng,
        Hệ thống Tự động
        """
        
    msg = Message(subject, recipients=[recipient_email])
    msg.body = body
    
    try:
        mail.send(msg)
        print(f"Gửi email thành công cho {recipient_email}")
    except Exception as e:
        print(f"LỖI GỬI EMAIL cho {recipient_email}: {e}")
        

# --- Parser regex fallback (giữ nguyên) ---
def parse_ocr(text):
    # ... (giữ nguyên logic parse_ocr) ...
    data = {
        'ho_ten': None,
        'ma_nv': None,
        'phong_ban': None,
        'loai_don': None,
        'ngay_bat_dau': None,
        'ngay_ket_thuc': None,
        'ly_do': None
    }
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Định nghĩa Regex cho các ký tự viết hoa tiếng Việt
    VIETNAMESE_CAPITAL = r'[A-ZÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪÉÈẺẼÊỀẾỆỂỄIÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮYÝỴỶỸ]'
    VIETNAMESE_LOWER = r'[a-zàáạảãăằắặẳẵâầấậẩẫéèẻẽêềếệểễiíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữyýỵỷỹ]'
    
    for line in lines:
        lower = line.lower()
        no_space_lower = lower.replace(' ', '')
        
        # --- Ho ten (Trích xuất tên bằng cách tìm các từ viết hoa liên tiếp) ---
        name_keywords = ['tên tôi là', 'tôi là', 'tôi tên là', 'họ tên', 'tôi là:']
        if data['ho_ten'] is None and any(keyword in lower for keyword in name_keywords):
            
            # 1. Tách chuỗi sau dấu phân cách (nếu có)
            parts = re.split(r'[:\-–]', line, maxsplit=1)
            name_candidate = parts[1].strip() if len(parts) > 1 else line.strip()

            # 2. Loại bỏ các từ khóa không cần thiết (Tên tôi là: / Tôi là)
            name_candidate = re.sub(r'(Tên tôi là|Tôi tên là|Tôi là|Họ tên)\s*[:\s\-–]*', '', name_candidate, flags=re.IGNORECASE).strip()
            
            # 3. CHỈ LẤY CÁC TỪ CÓ CHỮ CÁI ĐẦU VIẾT HOA LIÊN TIẾP (Tối đa 5 từ)
            intro_filter = r'tôi\s*viết.*|đơn\s*này\s*xin\s*phép.*|xin\s*phép\s*ban\s*lãnh\s*đạo.*|tôi\s*đề\s*nghị.*'
            name_candidate = re.sub(intro_filter, '', name_candidate, flags=re.IGNORECASE).strip()
            name_regex = r'(' + VIETNAMESE_CAPITAL + VIETNAMESE_LOWER + r'+\s*){1,5}'
            match = re.search(name_regex, name_candidate)
            
            if match:
                data['ho_ten'] = match.group(0).strip()
                continue
                
        # --- Mã NV (Tăng độ linh hoạt của Regex) ---
        if data['ma_nv'] is None:
            match = re.search(r'(mã\s*n\s*v|ma\s*n\s*v|mã\s*nhân\s*viên|manv)\s*[:\s\-–]*\s*([A-Za-z0-9\-_/]+)', line, re.IGNORECASE)
            if match:
                data['ma_nv'] = match.group(2).strip()

        # --- Phòng ban ---
        if data['phong_ban'] is None and ('phòng' in no_space_lower or 'phong' in no_space_lower):
            parts = re.split(r'[:\-–]', line, maxsplit=1)
            if len(parts) > 1:
                data['phong_ban'] = parts[1].strip()
            else:
                m = re.search(r'(phòng|phong)\s*(.+)', lower)
                if m:
                    data['phong_ban'] = m.group(2).strip()

        # --- Loại đơn (Giữ nguyên logic cũ) ---
        if data['loai_don'] is None:
            if re.search(r'nghỉ\s*phép|nghỉ\s*hàng\s*năm|xin\s*nghỉ|nghiphep|nghi\s*phep', no_space_lower, re.IGNORECASE):
                data['loai_don'] = 'Nghỉ phép'
            elif re.search(r'công\s*tác|đề\s*nghị\s*công\s*tác|congtac', no_space_lower, re.IGNORECASE):
                data['loai_don'] = 'Đề nghị Công tác'

        # --- Ngày (Giữ nguyên logic cũ) ---
        if data['ngay_bat_dau'] is None or data['ngay_ket_thuc'] is None:
            date_pattern = r'(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)'
            
            if data['ngay_bat_dau'] is None:
                match_start = re.search(r'(từ\s*ngay|từ\s*ngày)\s*[:\s\-–]*\s*' + date_pattern, lower)
                if match_start:
                    data['ngay_bat_dau'] = match_start.group(2).replace('-', '/')
                    
            if data['ngay_ket_thuc'] is None:
                match_end = re.search(r'(đến\s*ngay|đến\s*ngày)\s*[:\s\-–]*\s*' + date_pattern, lower)
                if match_end:
                    data['ngay_ket_thuc'] = match_end.group(2).replace('-', '/')
            
            if data['ngay_bat_dau'] is None or data['ngay_ket_thuc'] is None:
                date_match = re.search(r'(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)', line)
                if date_match:
                    dt = date_match.group(1).replace('-', '/')
                    if data['ngay_bat_dau'] is None:
                        data['ngay_bat_dau'] = dt
                    elif data['ngay_ket_thuc'] is None:
                        if dt != data['ngay_bat_dau']:
                            data['ngay_ket_thuc'] = dt

        # --- Lý do ---
        if data['ly_do'] is None and ('lý do' in lower or 'ly do' in lower or 'lýdo' in lower):
            ly_do_keywords = r'(lý do|ly do|lýdo)\s*[:\s\-–]*\s*'
            ly_do_content = ""
            
            parts = re.split(r'[:\-–]', line, maxsplit=1)
            if len(parts) > 1:
                ly_do_content = parts[1].strip()
            else:
                m = re.search(ly_do_keywords + r'(.+)', lower)
                if m:
                    ly_do_content = m.group(2).strip()
            
            if ly_do_content:
                ly_do_content = re.sub(r'kính\s*mong.*|chân\s*thành\s*cảm\s*ơn.*', '', ly_do_content, flags=re.IGNORECASE).strip()
                data['ly_do'] = ly_do_content
    return data

# --- Rule engine để quyết định bước duyệt tiếp theo (giữ nguyên) ---
# app.py

def decide_next_step(data):
    # 1. Lấy tên phòng ban từ dữ liệu đơn.
    phong_ban = (data.get('phong_ban') or '').strip()
    
    # ⚠️ SỬA CHỮA LỖI DẤU: Loại bỏ dấu tiếng Việt, sau đó chuyển thành chữ thường.
    # Ví dụ: "Phòng Kinh doanh" -> "Phong Kinh doanh"
    phong_normalized_ascii = unidecode(phong_ban).lower()
    
    # Thay thế khoảng trắng bằng dấu gạch dưới.
    # Ví dụ: "Phong Kinh doanh" -> "phong_kinh_doanh"
    phong_safe_code = phong_normalized_ascii.replace(' ', '_')
    
    # 2. Định dạng người duyệt tiếp theo: quan_ly_cua_[phong_ban_khong_dau]
    # Kết quả sẽ là: 'quan_ly_cua_phong_kinh_doanh' (không có dấu)
    next_approver_role = f'quan_ly_cua_{phong_safe_code}'
        
    return (next_approver_role, None) 

# --- Xác thực & phân quyền (giữ nguyên) ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# --- Các routes khác (giữ nguyên) ---
@app.route('/don-tu', methods=['GET', 'POST'])
def don_tu():
    username = session.get('username', 'Khách')
    if request.method == 'POST':
        return "Đơn đã được gửi!"
    return render_template('don_tu.html', username=username)

@app.route("/quanlynhanvien")
def quan_ly_nhan_vien():
    role = session.get("role")
    phong_ban = session.get("phong_ban")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if role == "giam_doc":
        cursor.execute("SELECT id, ho_ten, phong_ban, chuc_vu FROM users")
    elif role == "quan_ly":
        cursor.execute("SELECT id, ho_ten, phong_ban, chuc_vu FROM users WHERE phong_ban = ?", (phong_ban,))
    else:
        cursor.execute("SELECT id, ho_ten, phong_ban, chuc_vu FROM users WHERE id = ?", (session["user_id"],))

    nhanviens = cursor.fetchall()
    conn.close()

    return render_template("quan_ly_nhan_vien.html", nhanviens=nhanviens, role=role)

@app.route('/quan_ly_don', methods=['GET'])
@login_required
def quan_ly_don():
    conn = get_db_connection()
    search_query = request.args.get('search', '')
    phong_ban_filter = request.args.get('phong_ban_filter', '')
    trang_thai_filter = request.args.get('trang_thai_filter', '') 
    
    phong_bans_result = conn.execute("SELECT DISTINCT phong_ban FROM users WHERE phong_ban IS NOT NULL AND phong_ban != '' ORDER BY phong_ban").fetchall()
    phong_bans = [row['phong_ban'] for row in phong_bans_result]
    
    sql_base = "SELECT d.* FROM Don d JOIN users u ON d.user_id = u.id WHERE 1=1"
    params = []

    if phong_ban_filter:
        sql_base += " AND u.phong_ban = ?"
        params.append(phong_ban_filter)

    if trang_thai_filter:
        if trang_thai_filter == 'từ chối':
            sql_base += " AND LOWER(d.trang_thai) LIKE ?"
            params.append('%từ chối%')
        elif trang_thai_filter == 'đã duyệt':
            sql_base += " AND LOWER(d.trang_thai) = 'Đã duyệt'"
        elif trang_thai_filter == 'chờ duyệt':
            sql_base += " AND LOWER(d.trang_thai) = 'chờ duyệt'"
        elif trang_thai_filter == 'hoàn tất':
            sql_base += " AND LOWER(d.trang_thai) = 'Đã duyệt'"

    if search_query:
        search_like = f'%{search_query}%'
        sql_base += " AND (d.ho_ten LIKE ? OR d.ma_nv LIKE ? OR d.loai_don LIKE ?)"
        params.extend([search_like, search_like, search_like])
    
    sql_base += " ORDER BY d.id DESC" 
    
    dons = conn.execute(sql_base, params).fetchall()
    conn.close()

    return render_template('quan_ly_don.html', 
                            dons=dons, 
                            search_query=search_query,
                            phong_bans=phong_bans)

@app.route('/thongke')
@login_required
def thong_ke():
    conn = get_db_connection()
    
    total_submitted = conn.execute("SELECT COUNT(id) AS total FROM Don").fetchone()['total']
    total_approved = conn.execute("SELECT COUNT(id) AS total FROM Don WHERE LOWER(trang_thai) = 'Đã duyệt'").fetchone()['total']
    total_rejected = conn.execute("SELECT COUNT(id) AS total FROM Don WHERE LOWER(trang_thai) LIKE 'từ chối%'").fetchone()['total']
    total_waiting = conn.execute("SELECT COUNT(id) AS total FROM Don WHERE LOWER(trang_thai) = 'chờ duyệt'").fetchone()['total']
    
    avg_time_days = 0 
    approval_rate = (total_approved / total_submitted * 100) if total_submitted > 0 else 0

    type_data = conn.execute("""
    SELECT 
        CASE 
            WHEN loai_don IS NULL OR TRIM(loai_don) = '' THEN 'Chưa phân loại' 
            ELSE loai_don 
        END AS loai_don_clean, 
        COUNT(id) AS count 
    FROM Don 
    GROUP BY loai_don_clean
    ORDER BY count DESC
    """).fetchall()

    by_type_labels = [row['loai_don_clean'] for row in type_data]
    by_type_values = [row['count'] for row in type_data]

    waiting_by_approver = conn.execute("""
        SELECT nguoi_duyet_hien_tai AS name, COUNT(id) AS count
        FROM Don 
        WHERE LOWER(trang_thai) = 'chờ duyệt' AND nguoi_duyet_hien_tai IS NOT NULL
        GROUP BY nguoi_duyet_hien_tai
    """).fetchall()
    
    waiting_stats = [{'name': row['name'], 'count': row['count'], 'avg_tat': 0.0} 
                     for row in waiting_by_approver]

    approval_by_dept = conn.execute("""
        SELECT 
            u.phong_ban AS name,
            SUM(CASE WHEN LOWER(d.trang_thai) = 'Đã duyệt' THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN LOWER(d.trang_thai) LIKE 'từ chối%' THEN 1 ELSE 0 END) AS rejected
        FROM users u
        JOIN Don d ON u.id = d.user_id
        WHERE u.phong_ban IS NOT NULL AND d.trang_thai IS NOT NULL
        GROUP BY u.phong_ban
        ORDER BY u.phong_ban
    """).fetchall()

    trend_data = conn.execute("""
        SELECT 
            SUBSTR(ngay_gui, 1, 7) AS month_year, 
            
            SUM(
                JULIANDAY(SUBSTR(ngay_ket_thuc, 7, 4) || '-' || SUBSTR(ngay_ket_thuc, 4, 2) || '-' || SUBSTR(ngay_ket_thuc, 1, 2)) - 
                JULIANDAY(SUBSTR(ngay_bat_dau, 7, 4) || '-' || SUBSTR(ngay_bat_dau, 4, 2) || '-' || SUBSTR(ngay_bat_dau, 1, 2)) + 1 
            ) AS total_days
        
        FROM Don
        WHERE LOWER(trang_thai) = 'Đã duyệt' AND ngay_bat_dau IS NOT NULL AND ngay_ket_thuc IS NOT NULL
        GROUP BY month_year
        ORDER BY month_year DESC
        LIMIT 6 
    """).fetchall()

    trend_labels = [row['month_year'] for row in trend_data]
    
    trend_values = [round(row['total_days']) if row['total_days'] is not None else 0
                    for row in trend_data]

    trend_labels.reverse()
    trend_values.reverse()
    
    conn.close()

    stats = {
        'approval_rate': round(approval_rate, 2),
        'avg_time_days': round(avg_time_days, 1),
        'total_submitted': total_submitted,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'total_waiting': total_waiting, 
        'by_type_labels': by_type_labels,
        'by_type_values': by_type_values,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
        'waiting_by_approver': waiting_stats,
        'approval_by_dept': approval_by_dept
    }

    return render_template('thong_ke.html', stats=stats)

@app.route('/them_nhan_vien', methods=['GET', 'POST'])
@login_required
def them_nhan_vien():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ho_ten = request.form.get('ho_ten')
        ma_nv = request.form.get('ma_nv')
        phong_ban = request.form.get('phong_ban')
        chuc_vu = request.form.get('chuc_vu')
        role = request.form.get('role')
        email = request.form.get('email')
        
        if not username or not password:
            flash("Lỗi: Tên đăng nhập và Mật khẩu là bắt buộc.", 'error')
            return redirect(url_for('them_nhan_vien'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users 
                (username, password, ho_ten, ma_nv, phong_ban, chuc_vu, role, email) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, ho_ten, ma_nv, phong_ban, chuc_vu, role, email))
            
            conn.commit()
            
            flash(f"Đã thêm nhân viên {ho_ten} thành công!", 'success')
            return redirect(url_for('quan_ly_nhan_vien'))

        except sqlite3.IntegrityError:
            flash("Lỗi: Tên đăng nhập hoặc Mã nhân viên đã tồn tại.", 'error')
            return render_template('them_nhan_vien.html', data=request.form)

        except Exception as e:
            flash(f"Lỗi không xác định khi thêm nhân viên: {e}", 'error')
            return render_template('them_nhan_vien.html', data=request.form)
        finally:
            conn.close()
    
    return render_template('them_nhan_vien.html', data={})

@app.route('/sua_nhan_vien/<int:nv_id>', methods=['GET', 'POST'])
@login_required
def sua_nhan_vien(nv_id):
    conn = get_db_connection()
    nv = conn.execute('SELECT * FROM users WHERE id = ?', (nv_id,)).fetchone()
    
    if nv is None:
        conn.close()
        flash("Không tìm thấy nhân viên.")
        return redirect(url_for('quan_ly_nhan_vien'))

    if request.method == 'POST':
        ho_ten = request.form.get('ho_ten')
        ma_nv = request.form.get('ma_nv')
        phong_ban = request.form.get('phong_ban')
        chuc_vu = request.form.get('chuc_vu')
        role = request.form.get('role')
        email = request.form.get('email')
        new_password = request.form.get('password')

        update_fields = [
            'ho_ten = ?', 'ma_nv = ?', 'phong_ban = ?', 
            'chuc_vu = ?', 'role = ?', 'email = ?'
        ]
        update_params = [ho_ten, ma_nv, phong_ban, chuc_vu, role, email]

        if new_password:
            hashed_password = generate_password_hash(new_password)
            update_fields.append('password = ?')
            update_params.append(hashed_password)

        update_params.append(nv_id)
        
        sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"

        try:
            conn.execute(sql, update_params)
            conn.commit()

            if session.get('user_id') == nv_id:
                session['username'] = ho_ten
                session['phong_ban'] = phong_ban
                session['ma_nv'] = ma_nv
                session['email'] = email

            conn.close()
            flash(f"Đã cập nhật thông tin nhân viên {ho_ten} thành công!")
            return redirect(url_for('quan_ly_nhan_vien'))
            
        except sqlite3.IntegrityError:
            conn.close()
            flash("Lỗi: Mã nhân viên đã tồn tại (hoặc username nếu bạn sửa).", 'error')
            nv_dict = dict(nv)
            nv_dict.update(request.form)
            return render_template('sua_nhan_vien.html', nv=nv_dict)

        except Exception as e:
            conn.close()
            flash(f"Lỗi không xác định khi sửa nhân viên: {e}", 'error')
            return redirect(url_for('quan_ly_nhan_vien'))
        
    conn.close()
    return render_template('sua_nhan_vien.html', nv=nv)

@app.route('/xoa_nhan_vien/<int:nv_id>', methods=['POST'])
@login_required
def xoa_nhan_vien(nv_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (nv_id,))
    conn.commit()
    conn.close()
    flash(f"Đã xóa nhân viên ID {nv_id}.")
    return redirect(url_for('quan_ly_nhan_vien'))

@app.route('/tu_choi_don/<int:don_id>', methods=['POST'])
@login_required
def tu_choi_don(don_id):
    role = session.get('role')
    user_id = session['user_id']
    thoi_gian_duyet = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ⚠️ 1. LẤY LÝ DO TỪ FORM/MODAL
    ly_do_tu_choi = request.form.get('ly_do_tu_choi', 'Người duyệt không cung cấp lý do chi tiết.')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 2. LẤY THÔNG TIN ĐƠN & EMAIL NGƯỜI NỘP (Cần JOIN để lấy email)
    query = """
        SELECT d.loai_don, d.user_id, u.email 
        FROM Don d JOIN users u ON d.user_id = u.id 
        WHERE d.id = ?
    """
    don = cursor.execute(query, (don_id,)).fetchone()
    
    if not don:
        conn.close()
        flash("Không tìm thấy đơn!")
        return redirect(url_for('dashboard_duyet'))
        
    nguoi_tao_don_id = don['user_id']
    loai_don = don['loai_don']
    nguoi_nop_email = don['email']
    
    # Chuẩn bị nội dung ghi log (chứa lý do chi tiết)
    ghi_chu_log = f'Đã từ chối tại cấp {role}. Lý do: {ly_do_tu_choi}'

    # 3. Cập nhật trạng thái và Ghi Log Duyệt
    cursor.execute('''
        UPDATE Don 
        SET trang_thai = 'Từ chối', nguoi_duyet_hien_tai = 'Đã Từ chối'
        WHERE id = ?
    ''', (don_id,))

    # Ghi Log Duyệt (chỉ 1 lần)
    cursor.execute('''
        INSERT INTO DuyetLog (don_id, user_id, thoi_gian, phe_duyet, ghi_chu)
        VALUES (?, ?, ?, ?, ?)
    ''', (don_id, user_id, thoi_gian_duyet, 'tu_choi', ghi_chu_log))

    # 4. TẠO THÔNG BÁO TỪ CHỐI CHO NHÂN VIÊN (BẢNG THONGBAO)
    
    # Dịch tên vai trò người từ chối thân thiện
    role_display = {
        'quan_ly': 'Quản lý',
        'nhan_su': 'Phòng Nhân sự',
        'ke_toan': 'Phòng Kế toán',
        'giam_doc': 'Ban Giám đốc'
    }.get(role.lower(), role.upper())
    
    # Nội dung thông báo cho người nộp đơn (đã bao gồm lý do)
    thong_bao_noi_dung = (
        f'❌ Đơn ID {don_id} ({loai_don}) của bạn đã bị TỪ CHỐI bởi {role_display}. Lý do: {ly_do_tu_choi}'
    )

    cursor.execute('''
        INSERT INTO ThongBao (user_id, don_id, noi_dung, da_doc)
        VALUES (?, ?, ?, 0)
    ''', (nguoi_tao_don_id, don_id, thong_bao_noi_dung))

    # 5. GỬI EMAIL TỪ CHỐI (BỔ SUNG)
    if nguoi_nop_email:
        send_approval_email(
            recipient_email=nguoi_nop_email, 
            don_id=don_id, 
            don_type=loai_don, 
            trang_thai='tu_choi', 
            ghi_chu=ghi_chu_log # Gửi toàn bộ nội dung log
        )

    conn.commit()
    conn.close()

    # 6. FLASH CHO NGƯỜI DUYỆT
    flash(f'Đơn đã bị từ chối thành công. Lý do: {ly_do_tu_choi}')
    return redirect(url_for('dashboard_duyet'))

@app.route('/don/<int:don_id>')
@login_required
def don_details(don_id):
    user_id = session.get('user_id') # Lấy ID người dùng hiện tại
    conn = get_db_connection()
    
    # 1. Lấy dữ liệu đơn chính
    don = conn.execute('SELECT * FROM Don WHERE id = ?', (don_id,)).fetchone()
    
    if not don:
        conn.close()
        flash("Không tìm thấy đơn!")
        return redirect(url_for('dashboard'))

    # 2. BỔ SUNG: Lấy Lý do từ chối cuối cùng (Nếu có)
    ly_do_tu_choi_log = conn.execute('''
        SELECT ghi_chu, thoi_gian 
        FROM DuyetLog 
        WHERE don_id = ? AND phe_duyet = 'tu_choi'
        ORDER BY id DESC LIMIT 1
    ''', (don_id,)).fetchone()
    
    # 3. Đánh dấu thông báo liên quan là đã đọc
    # Chỉ đánh dấu nếu người đang xem là người nộp đơn (chủ sở hữu thông báo)
    if don['user_id'] == user_id:
        try:
            conn.execute('''
                UPDATE ThongBao
                SET da_doc = 1
                WHERE user_id = ? AND don_id = ? AND da_doc = 0
            ''', (user_id, don_id))
            conn.commit()
        except Exception as e:
            print(f"Warning: Lỗi khi đánh dấu thông báo đơn {don_id} là đã đọc: {e}")
            
    conn.close()

    return render_template(
        'don_detail.html', 
        don=don, 
        don_id=don_id, 
        ly_do_tu_choi_log=ly_do_tu_choi_log # Truyền log lý do vào template
    )

@app.route('/caidat')
def cai_dat():
    return render_template('cai_dat.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username'] 
            session['ho_ten'] = user['ho_ten'] or user['username']
            session['ma_nv'] = user['ma_nv']
            session['phong_ban'] = user['phong_ban']
            session['email'] = user['email']
            session['chuc_vu'] = user['chuc_vu']
            
            return redirect(url_for('dashboard'))
            
        flash('Tên đăng nhập hoặc mật khẩu không đúng')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'nhan_vien':
        return redirect(url_for('dashboard_nhanvien'))
    else:
        return redirect(url_for('dashboard_duyet'))

@app.route('/dashboard/nhanvien')
@login_required
def dashboard_nhanvien():
    user_id = session['user_id']
    conn = get_db_connection()
    dons = conn.execute('SELECT * FROM Don WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('dashboard_nhanvien.html', dons=dons)


# app.py (Cần có: from unidecode import unidecode ở đầu file)

@app.route('/dashboard/duyet')
@login_required
def dashboard_duyet():
    role = session.get('role')
    phong = session.get('phong_ban') 
    
    filter_mode = request.args.get('filter')
    search_query = request.args.get('search')

    # 1. TẠO ROLE ĐƯỢC CHUẨN HÓA CHO BỘ LỌC (ROLE_FILTER)
    if role == 'quan_ly':
        # ⚠️ SỬA CHỮA: LOẠI BỎ DẤU, CHUYỂN CHỮ THƯỜNG, VÀ THAY THẾ KHOẢNG TRẮNG
        phong_ascii = unidecode(phong or '').lower()
        phong_normalized_safe = phong_ascii.replace(' ', '_')
        
        # Vai trò được mã hóa không dấu: 'quan_ly_cua_phong_kinh_doanh'
        role_filter = f'quan_ly_cua_{phong_normalized_safe}'
    else:
        # Các vai trò khác vẫn dùng tên vai trò đơn thuần
        role_filter = role.strip().lower()

    conn = get_db_connection()
    
    # ----------------------------------------------------
    # TÍNH TOÁN THỐNG KÊ (Giữ nguyên)
    # ----------------------------------------------------
    don_waiting = conn.execute(
        "SELECT COUNT(id) AS total FROM Don WHERE LOWER(trang_thai) = 'chờ duyệt'"
    ).fetchone()['total']

    don_approved = conn.execute(
        "SELECT COUNT(id) AS total FROM Don WHERE LOWER(trang_thai) = 'Đã duyệt'"
    ).fetchone()['total']

    don_rejected = conn.execute(
        "SELECT COUNT(id) AS total FROM Don WHERE LOWER(trang_thai) LIKE 'từ chối%'"
    ).fetchone()['total']
    
    
    # ----------------------------------------------------
    # LỌC DỮ LIỆU BẢNG (Sử dụng role_filter)
    # ----------------------------------------------------

    sql_base = "SELECT * FROM Don WHERE 1=1" 
    params = []
    
    if filter_mode == 'waiting':
        # Lọc theo vai trò/mã hóa đã chuẩn hóa (role_filter)
        if role in ['quan_ly', 'nhan_su', 'ke_toan', 'giam_doc']:
            sql_base += " AND LOWER(trang_thai) = 'chờ duyệt' AND nguoi_duyet_hien_tai = ?"
            params.append(role_filter)
            
    # Xử lý tìm kiếm (Giữ nguyên)
    if search_query:
        search_like = f'%{search_query}%'
        sql_base += " AND (ho_ten LIKE ? OR ma_nv LIKE ?)" 
        params.extend([search_like, search_like])
    
    sql_base += " ORDER BY id DESC LIMIT 5" 
    dons = conn.execute(sql_base, params).fetchall()

    conn.close()

    return render_template(
        'dashboard_duyet.html',
        dons=dons, 
        don_waiting=don_waiting,
        don_approved=don_approved, 
        don_rejected=don_rejected, 
        current_filter=filter_mode,
        role_filter=role_filter  # QUAN TRỌNG: Truyền biến này để template dùng
    )

# app.py (Cần đảm bảo có: from unidecode import unidecode ở đầu file)

# app.py (Cần có: from unidecode import unidecode ở đầu file)
# ... (các hàm khác)

@app.route('/duyet_don/<int:don_id>', methods=['POST'])
@login_required
def duyet_don(don_id):
    role = session.get('role')
    user_id = session.get('user_id')
    thoi_gian_duyet = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cursor = conn.cursor()

    # BỔ SUNG: Truy vấn để lấy email người nộp đơn
    query = """
        SELECT 
            d.trang_thai, d.nguoi_duyet_hien_tai, d.loai_don, d.user_id, u.email 
        FROM Don d JOIN users u ON d.user_id = u.id 
        WHERE d.id = ?
    """
    don = cursor.execute(query, (don_id,)).fetchone()
    
    if not don:
        flash("Không tìm thấy đơn.")
        conn.close()
        return redirect(url_for('dashboard_duyet'))

    current_status = (don['trang_thai'] or '').strip().lower()
    current_approver = (don['nguoi_duyet_hien_tai'] or '').strip().lower()
    loai_don = (don['loai_don'] or '').strip().lower()
    role_normalized = role.strip().lower()
    nguoi_tao_don_id = don['user_id']
    nguoi_nop_email = don['email'] # << LẤY EMAIL CHO CHỨC NĂNG MAIL
    
    # --- Định nghĩa Map dịch vai trò ---
    approver_display_map = {
        'nhan_su': 'Phòng Nhân sự',
        'ke_toan': 'Phòng Kế toán',
        'giam_doc': 'Ban Giám đốc',
        'hoan_tat': 'Hoàn tất'
    }

    # 1. TẠO ROLE CỦA NGƯỜI ĐANG DUYỆT ĐỂ SO SÁNH CHÍNH XÁC (PHIÊN BẢN KHÔNG DẤU)
    if role_normalized == 'quan_ly':
        phong_ascii = unidecode(session.get('phong_ban') or '').lower()
        phong_normalized_safe = phong_ascii.replace(' ', '_')
        session_approver_role = f'quan_ly_cua_{phong_normalized_safe}'
        current_approver_display = f"Quản lý Phòng {session.get('phong_ban', '...')}"
    else:
        session_approver_role = role_normalized 
        current_approver_display = approver_display_map.get(role, role.upper())

    # 2. KIỂM TRA TÍNH HỢP LỆ
    if current_status != 'chờ duyệt' or current_approver != session_approver_role:
        flash("Đơn không hợp lệ, đã được xử lý, hoặc không chờ bạn duyệt (Chỉ Quản lý phòng ban đó được duyệt).")
        conn.close()
        return redirect(url_for('dashboard_duyet'))

    # Khởi tạo trạng thái duyệt mới
    new_status = 'chờ duyệt'
    next_approver = current_approver
    log_ghi_chu = f'Đã duyệt tại cấp {current_approver_display}'
    
    # --- Định nghĩa Loại Đơn (Giữ nguyên) ---
    is_cong_tac = 'công tác' in loai_don or 'congtac' in loai_don
    is_nghi_phep = 'nghỉ' in loai_don or 'nghiphep' in loai_don
    is_thanh_toan = 'thanh toán' in loai_don or 'thanhtoan' in loai_don
    is_thoi_viec = 'thôi việc' in loai_don
    
    flow_handled = False
    
    # =========================================================================
    # LOGIC CHUYỂN CẤP
    # =========================================================================
    
    if current_approver.startswith('quan_ly_cua_'): 
        if is_thoi_viec:
            next_approver = 'nhan_su'
        elif is_cong_tac:
            next_approver = 'giam_doc'
        elif is_thanh_toan:
            next_approver = 'ke_toan'
        else: 
            new_status = 'Đã duyệt'
            next_approver = 'hoàn tất'
        flow_handled = True
    
    elif current_approver == 'nhan_su':
        if is_thoi_viec:
            next_approver = 'giam_doc'
        else:
            new_status = 'Đã duyệt'
            next_approver = 'hoàn tất'
        flow_handled = True
        
    elif current_approver == 'ke_toan' or current_approver == 'giam_doc':
        new_status = 'Đã duyệt'
        next_approver = 'hoàn tất'
        flow_handled = True
        
    # ... (Xử lý lỗi không tìm thấy luồng giữ nguyên) ...


    # 2. Cập nhật DB (Bảng Don và DuyetLog)
    cursor.execute('''
        UPDATE Don 
        SET trang_thai = ?, nguoi_duyet_hien_tai = ?
        WHERE id = ?
    ''', (new_status, next_approver, don_id))

    cursor.execute('''
        INSERT INTO DuyetLog (don_id, user_id, thoi_gian, phe_duyet, ghi_chu)
        VALUES (?, ?, ?, ?, ?)
    ''', (don_id, user_id, thoi_gian_duyet, 'duyet', log_ghi_chu))

    
    # =========================================================================
    # 3. TẠO THÔNG BÁO CHO NHÂN VIÊN & GỬI EMAIL
    # =========================================================================
    
    if new_status == 'Đã duyệt':
        thong_bao_noi_dung = f'✅ Đơn ID {don_id} ({don["loai_don"]}) đã được DUYỆT HOÀN TẤT!'
        flash_msg = 'Đơn đã được duyệt hoàn tất.'
        
        # GỬI EMAIL KHI DUYỆT HOÀN TOÀN
        if nguoi_nop_email:
             send_approval_email(nguoi_nop_email, don_id, don['loai_don'], 'duyet', log_ghi_chu)
             
    else: # new_status == 'chờ duyệt' (Tức là chuyển cấp)
        thong_bao_noi_dung = f'⏳ Đơn ID {don_id} ({don["loai_don"]}) đã được duyệt và chuyển cấp.'
        flash_msg = 'Đơn đã được duyệt và chuyển sang cấp tiếp theo.'

    cursor.execute('''
        INSERT INTO ThongBao (user_id, don_id, noi_dung, da_doc)
        VALUES (?, ?, ?, 0)
    ''', (nguoi_tao_don_id, don_id, thong_bao_noi_dung))
    
    conn.commit()
    conn.close()
    
    flash(flash_msg)
    return redirect(url_for('dashboard_duyet'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    
    # 1. LẤY THÔNG TIN MẶC ĐỊNH CHO FORM (default_data)
    user_ho_ten = session.get('ho_ten')
    user_ma_nv = session.get('ma_nv')
    user_phong_ban = session.get('phong_ban')
    
    default_data = {
        'ho_ten': user_ho_ten,
        'ma_nv': user_ma_nv,
        'phong_ban': user_phong_ban,
        'loai_don': None,
        'ngay_bat_dau': None,
        'ngay_ket_thuc': None,
        'ly_do': None
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # BỔ SUNG: LẤY DANH SÁCH ĐƠN CỦA NHÂN VIÊN (Để hiển thị trạng thái)
    # Chúng ta chỉ cần thông tin cơ bản: ID, loại đơn, trạng thái, và người duyệt hiện tại
    dons = cursor.execute('''
        SELECT id, loai_don, trang_thai, ngay_gui, nguoi_duyet_hien_tai 
        FROM Don WHERE user_id = ? 
        ORDER BY id DESC LIMIT 5
    ''', (user_id,)).fetchall()
    
    # BỔ SUNG: LẤY THÔNG BÁO CHO NHÂN VIÊN
    notifications = cursor.execute('''
        SELECT id, noi_dung, thoi_gian, da_doc, don_id 
        FROM ThongBao 
        WHERE user_id = ? 
        ORDER BY da_doc ASC, thoi_gian DESC 
        LIMIT 15
    ''', (user_id,)).fetchall()
    
    conn.close()

    if request.method == 'POST':
        mode = request.form.get('mode')
        
        if mode == 'upload':
            file = request.files.get('file')
            if not file or file.filename == '':
                flash('Chưa chọn file')
                return redirect(request.url)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            dest = os.path.join(STATIC_UPLOAD_FOLDER, filename)
            try:
                with open(filepath, 'rb') as fr, open(dest, 'wb') as fw:
                    fw.write(fr.read())
            except Exception as e:
                print("Error copying file to static:", e)

            # Extract text + try Gemini parse
            cleaned_text, parsed = extract_text(filepath, use_gemini=True)
            if parsed is None:
                # fallback to regex parser
                parsed = parse_ocr(cleaned_text)

            # --- BỔ SUNG: HỢP NHẤT DỮ LIỆU CÁ NHÂN VỚI KẾT QUẢ OCR ---
            final_data = default_data.copy()
            for key in final_data:
                if parsed.get(key) is not None:
                    final_data[key] = parsed[key]
            
            next_step, _ = decide_next_step(final_data)
            return render_template(
                'confirm.html',
                data=final_data,
                filepath=filename,
                ket_qua_ocr=cleaned_text,
                next_step=next_step
            )

        else:  # nhập tay
            data = {
                'ho_ten': request.form.get('ho_ten'),
                'ma_nv': request.form.get('ma_nv'),
                'phong_ban': request.form.get('phong_ban'),
                'loai_don': request.form.get('loai_don'),
                'ngay_bat_dau': request.form.get('ngay_bat_dau'),
                'ngay_ket_thuc': request.form.get('ngay_ket_thuc'),
                'ly_do': request.form.get('ly_do')
            }
            # Điền các trường còn thiếu từ session nếu người dùng bỏ qua
            for key, value in default_data.items():
                if data.get(key) is None or data.get(key) == '':
                    data[key] = value

            next_step, _ = decide_next_step(data)
            return render_template('confirm.html', data=data, filepath=None, ket_qua_ocr='', next_step=next_step)
            
    # Xử lý GET Request (Hiển thị form)
    return render_template('index.html', 
        default_data=default_data, 
        notifications=notifications,
        dons=dons # TRUYỀN BIẾN ĐƠN VÀO TEMPLATE
    )

@app.route('/save', methods=['POST'])
@login_required
def save():
    user_id = session['user_id']
    ho_ten = request.form.get('ho_ten')
    ma_nv = request.form.get('ma_nv')
    phong_ban = request.form.get('phong_ban')
    loai_don = request.form.get('loai_don')
    ngay_bat_dau = request.form.get('ngay_bat_dau')
    ngay_ket_thuc = request.form.get('ngay_ket_thuc')
    ly_do = request.form.get('ly_do')
    filepath = request.form.get('filepath')
    ket_qua_ocr = request.form.get('ket_qua_ocr')

    if not ly_do and ket_qua_ocr:
        ocr_text = (ket_qua_ocr or '').lower()
        for tu in ['hiếu', 'hỷ', 'thai sản', 'ma chay', 'thai san', 'cưới', 'ăn hỏi', 'đám giỗ', 'tai nạn']:
            if tu in ocr_text:
                ly_do = tu
                break

    ly_do_lower = (ly_do or '').lower()
    if any(tu in ly_do_lower for tu in ['hiếu', 'hỷ', 'thai sản', 'ma chay', 'thai san', 'cưới', 'ăn hỏi', 'đám giỗ', 'tai nạn']):
        trang_thai = 'đã duyệt'
        nguoi_duyet_hien_tai = 'đã duyệt'
    else:
        nguoi_duyet_hien_tai = request.form.get('next_step') or 'quan_ly'
        trang_thai = 'chờ duyệt'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Don (
            user_id, ho_ten, ma_nv, phong_ban, loai_don,
            ngay_bat_dau, ngay_ket_thuc, ly_do,
            trang_thai, nguoi_duyet_hien_tai,
            file_goc, ket_qua_ocr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, ho_ten, ma_nv, phong_ban, loai_don,
        ngay_bat_dau, ngay_ket_thuc, ly_do,
        trang_thai, nguoi_duyet_hien_tai,
        filepath, ket_qua_ocr
    ))
    conn.commit()
    don_id = cursor.lastrowid
    conn.close()

    flash('Đơn đã lưu với trạng thái: ' + trang_thai)
    return redirect(url_for('don_detail', don_id=don_id))

@app.route('/don/<int:don_id>')
@login_required
def don_detail(don_id):
    conn = get_db_connection()
    don = conn.execute('SELECT * FROM Don WHERE id = ?', (don_id,)).fetchone()
    conn.close()
    if not don:
        flash('Không tìm thấy đơn')
        return redirect(url_for('dashboard'))
    return render_template('don_detail.html', don=don)

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(STATIC_UPLOAD_FOLDER, filename)


if __name__ == '__main__':
    if not os.path.exists('database.db'):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))