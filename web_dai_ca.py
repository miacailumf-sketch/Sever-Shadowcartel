from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, flash, jsonify
import os
import hashlib
import base64
from datetime import datetime
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = 'SHADOW_CARTEL_GTA5VN_2026_SECRET'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# ==================== CẤU HÌNH ====================
UPLOAD_BASE = 'shadow_uploads'
BACKGROUND_IMAGE = 'image_6.png'
os.makedirs(UPLOAD_BASE, exist_ok=True)

# Database
users_db = {
    "shadowcartel": {
        "password": hashlib.sha256("shadowcartel1012".encode()).hexdigest(),
        "role": "admin",
        "joined": datetime.now().strftime("%Y-%m-%d")
    }
}

# Lưu số ảnh đã gửi của từng user cho từng loại
user_stats = {
    "shadowcartel": {"graffiti": 0, "burglary": 0}
}

# Lưu danh sách ảnh của từng user
user_images = {
    "shadowcartel": {"graffiti": [], "burglary": []}
}

# ==================== HÀM HỖ TRỢ ====================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Vui lòng đăng nhập!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user') != 'shadowcartel':
            flash('Quyền truy cập bị từ chối!', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# ==================== GIAO DIỆN CSS ====================
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap');
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
        background: #000000 url('/bg_image') no-repeat center center fixed;
        background-size: cover;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        padding: 20px;
    }
    
    .glass {
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 28px;
        padding: 30px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .brand {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 4px;
        background: linear-gradient(135deg, #ffffff 0%, #888888 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        text-align: center;
        margin-bottom: 8px;
    }
    
    .sub-brand {
        font-size: 0.7rem;
        letter-spacing: 2px;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* 2 cột chính */
    .missions-container {
        display: flex;
        gap: 30px;
        flex-wrap: wrap;
    }
    
    .mission-card {
        flex: 1;
        min-width: 300px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 25px;
    }
    
    .mission-header {
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    
    .mission-icon {
        font-size: 3rem;
        margin-bottom: 10px;
    }
    
    .mission-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: 2px;
    }
    
    /* 2 bảng nhỏ trong mỗi mission */
    .stats-panel {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .stats-label {
        font-size: 0.7rem;
        color: #888;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .stats-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffaa00;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        margin-bottom: 20px;
    }
    
    .upload-area:hover {
        border-color: rgba(255, 255, 255, 0.5);
        background: rgba(255, 255, 255, 0.03);
    }
    
    .upload-icon {
        font-size: 2rem;
        margin-bottom: 10px;
    }
    
    .upload-text {
        font-size: 0.8rem;
        color: #888;
    }
    
    input[type="file"] {
        display: none;
    }
    
    /* Buttons */
    button {
        width: 100%;
        padding: 12px;
        background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
        border: none;
        border-radius: 14px;
        color: #000;
        font-weight: 700;
        cursor: pointer;
        transition: 0.3s;
        margin-top: 10px;
    }
    
    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
    }
    
    .logout-link {
        display: block;
        text-align: center;
        margin-top: 30px;
        color: #555;
        text-decoration: none;
        font-size: 0.7rem;
    }
    
    .logout-link:hover { color: #fff; }
    
    /* Flash messages */
    .flash-success {
        background: rgba(0,255,136,0.1);
        border: 1px solid #00ff88;
        color: #00ff88;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .flash-error {
        background: rgba(255,68,68,0.1);
        border: 1px solid #ff4444;
        color: #ff4444;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Admin image grid */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    
    .image-item {
        background: rgba(0,0,0,0.5);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    
    .image-item img {
        max-width: 100%;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    
    .image-info {
        font-size: 0.7rem;
        color: #888;
    }
    
    .admin-tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    
    .admin-tab {
        background: rgba(255,255,255,0.05);
        border: 1px solid #333;
        padding: 10px 20px;
        border-radius: 30px;
        cursor: pointer;
        transition: 0.3s;
    }
    
    .admin-tab.active {
        background: rgba(255,255,255,0.15);
        border-color: #fff;
    }
    
    .user-select {
        width: 100%;
        padding: 10px;
        background: rgba(255,255,255,0.05);
        border: 1px solid #333;
        border-radius: 12px;
        color: #fff;
        margin-bottom: 20px;
    }
    
    @media (max-width: 800px) {
        .missions-container { flex-direction: column; }
        .glass { padding: 20px; }
        .brand { font-size: 1.5rem; }
    }
</style>
"""

# ==================== ROUTES ====================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        if username in users_db and users_db[username]['password'] == hashlib.sha256(password.encode()).hexdigest():
            session.permanent = True
            session['user'] = username
            flash(f'Chào mừng {username.upper()}!', 'success')
            return redirect(url_for('admin' if username == 'shadowcartel' else 'dashboard'))
        
        flash('Sai tên đăng nhập hoặc mật khẩu!', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>SHADOW CARTEL | Đăng Nhập</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''
    </head>
    <body>
        <div class="glass" style="max-width: 450px;">
            <div class="brand">SHADOW CARTEL</div>
            <div class="sub-brand">GIAO THỨC TRUY CẬP</div>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="post">
                <input type="text" name="username" placeholder="TÊN ĐĂNG NHẬP" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;">
                <input type="password" name="password" placeholder="MẬT KHẨU" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;">
                <button type="submit">XÁC THỰC</button>
            </form>
            <a href="{{ url_for('register') }}" class="logout-link">ĐĂNG KÝ THÀNH VIÊN MỚI</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Vui lòng điền đầy đủ!', 'error')
        elif username in users_db:
            flash('Tên đã tồn tại!', 'error')
        else:
            users_db[username] = {
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "role": "member",
                "joined": datetime.now().strftime("%Y-%m-%d")
            }
            user_stats[username] = {"graffiti": 0, "burglary": 0}
            user_images[username] = {"graffiti": [], "burglary": []}
            session['user'] = username
            flash(f'Đăng ký thành công!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>SHADOW CARTEL | Đăng Ký</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''
    </head>
    <body>
        <div class="glass" style="max-width: 450px;">
            <div class="brand">GIA NHẬP</div>
            <div class="sub-brand">HỢP ĐỒNG ĐỆ TỬ</div>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="post">
                <input type="text" name="username" placeholder="TÊN ĐỆ TỬ MỚI" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;">
                <input type="password" name="password" placeholder="MẬT KHẨU" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;">
                <button type="submit">KÝ TÊN</button>
            </form>
            <a href="{{ url_for('login') }}" class="logout-link">← QUAY LẠI ĐĂNG NHẬP</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['user']
    stats = user_stats.get(username, {"graffiti": 0, "burglary": 0})
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>SHADOW CARTEL | Bảng Điều Khiển</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''
    </head>
    <body>
        <div class="glass">
            <div class="brand">SHADOW CARTEL</div>
            <div class="sub-brand">CHÀO MỪNG: {{ username.upper() }}</div>
            
            <div class="missions-container">
                <!-- XỊT SƠN -->
                <div class="mission-card">
                    <div class="mission-header">
                        <div class="mission-icon">🎨</div>
                        <div class="mission-title">XỊT SƠN</div>
                    </div>
                    
                    <div class="stats-panel">
                        <div class="stats-label">SỐ ẢNH ĐÃ GỬI</div>
                        <div class="stats-number">{{ stats.graffiti }}</div>
                    </div>
                    
                    <div class="upload-area" onclick="document.getElementById('file-graffiti').click()">
                        <div class="upload-icon">📤</div>
                        <div class="upload-text">NHẤP ĐỂ GỬI ẢNH XỊT SƠN</div>
                    </div>
                    <form id="form-graffiti" action="/upload" method="post" enctype="multipart/form-data" style="display:none;">
                        <input type="file" name="file" id="file-graffiti" accept="image/*" onchange="this.form.submit()">
                        <input type="hidden" name="type" value="graffiti">
                    </form>
                </div>
                
                <!-- TRỘM NHÀ -->
                <div class="mission-card">
                    <div class="mission-header">
                        <div class="mission-icon">🏠</div>
                        <div class="mission-title">TRỘM NHÀ</div>
                    </div>
                    
                    <div class="stats-panel">
                        <div class="stats-label">SỐ ẢNH ĐÃ GỬI</div>
                        <div class="stats-number">{{ stats.burglary }}</div>
                    </div>
                    
                    <div class="upload-area" onclick="document.getElementById('file-burglary').click()">
                        <div class="upload-icon">📤</div>
                        <div class="upload-text">NHẤP ĐỂ GỬI ẢNH TRỘM NHÀ</div>
                    </div>
                    <form id="form-burglary" action="/upload" method="post" enctype="multipart/form-data" style="display:none;">
                        <input type="file" name="file" id="file-burglary" accept="image/*" onchange="this.form.submit()">
                        <input type="hidden" name="type" value="burglary">
                    </form>
                </div>
            </div>
            
            <a href="{{ url_for('logout') }}" class="logout-link">[ NGẮT KẾT NỐI ]</a>
        </div>
    </body>
    </html>
    ''', username=username, stats=stats)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    username = session['user']
    mission_type = request.form.get('type')
    
    if mission_type not in ['graffiti', 'burglary']:
        flash('Loại nhiệm vụ không hợp lệ!', 'error')
        return redirect(url_for('dashboard'))
    
    if 'file' not in request.files:
        flash('Không có file nào được chọn!', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Không có file nào được chọn!', 'error')
        return redirect(url_for('dashboard'))
    
    # Lưu file
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
    filename = f"{username}_{mission_type}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_BASE, filename)
    file.save(filepath)
    
    # Cập nhật dữ liệu
    if username not in user_stats:
        user_stats[username] = {"graffiti": 0, "burglary": 0}
    if username not in user_images:
        user_images[username] = {"graffiti": [], "burglary": []}
    
    user_stats[username][mission_type] += 1
    user_images[username][mission_type].append({
        "filename": filename,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    flash(f'Đã gửi ảnh thành công! (+1 { "XỊT SƠN" if mission_type == "graffiti" else "TRỘM NHÀ" })', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@admin_required
def admin():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>SHADOW CARTEL | Admin</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''
    </head>
    <body>
        <div class="glass">
            <div class="brand">👑 BẢNG ĐIỀU HÀNH</div>
            <div class="sub-brand">QUẢN LÝ ĐỆ TỬ SHADOW CARTEL</div>
            
            <div class="admin-tabs">
                <div class="admin-tab active" onclick="showTab('users')">👥 DANH SÁCH ĐỆ TỬ</div>
                <div class="admin-tab" onclick="showTab('images')">🖼️ TẤT CẢ ẢNH ĐỆ TỬ</div>
            </div>
            
            <div id="tab-users">
                <select id="user-select" class="user-select" onchange="loadUserImages()">
                    <option value="">-- CHỌN ĐỆ TỬ --</option>
                    {% for user in users %}
                    <option value="{{ user }}">{{ user.upper() }}</option>
                    {% endfor %}
                </select>
                <div id="user-stats"></div>
                <div id="user-images" class="image-grid"></div>
            </div>
            
            <div id="tab-images" style="display:none;">
                <div class="image-grid" id="all-images-grid"></div>
            </div>
            
            <div style="margin-top: 30px; display: flex; gap: 15px;">
                <form action="/reset_all" method="post" style="flex:1;">
                    <button type="submit" style="background: #ff4444; color: white;">🔄 RESET TOÀN BỘ</button>
                </form>
                <a href="{{ url_for('dashboard') }}" style="flex:1;">
                    <button style="background: #333; color: white;">← VỀ BẢNG ĐIỀU KHIỂN</button>
                </a>
            </div>
            
            <a href="{{ url_for('logout') }}" class="logout-link">[ ĐĂNG XUẤT ]</a>
        </div>
        
        <script>
            const userData = {{ users_data|tojson }};
            const allImages = {{ all_images|tojson }};
            
            function showTab(tab) {
                if (tab === 'users') {
                    document.getElementById('tab-users').style.display = 'block';
                    document.getElementById('tab-images').style.display = 'none';
                    document.querySelectorAll('.admin-tab')[0].classList.add('active');
                    document.querySelectorAll('.admin-tab')[1].classList.remove('active');
                } else {
                    document.getElementById('tab-users').style.display = 'none';
                    document.getElementById('tab-images').style.display = 'block';
                    document.querySelectorAll('.admin-tab')[0].classList.remove('active');
                    document.querySelectorAll('.admin-tab')[1].classList.add('active');
                    loadAllImages();
                }
            }
            
            function loadUserImages() {
                const user = document.getElementById('user-select').value;
                const statsDiv = document.getElementById('user-stats');
                const imagesDiv = document.getElementById('user-images');
                
                if (!user || !userData[user]) {
                    statsDiv.innerHTML = '';
                    imagesDiv.innerHTML = '';
                    return;
                }
                
                const data = userData[user];
                statsDiv.innerHTML = `
                    <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                        <div class="stats-panel" style="flex:1;">
                            <div class="stats-label">🎨 XỊT SƠN</div>
                            <div class="stats-number">${data.graffiti_count}</div>
                        </div>
                        <div class="stats-panel" style="flex:1;">
                            <div class="stats-label">🏠 TRỘM NHÀ</div>
                            <div class="stats-number">${data.burglary_count}</div>
                        </div>
                    </div>
                `;
                
                let html = '';
                for (const img of data.graffiti) {
                    html += `
                        <div class="image-item">
                            <img src="/uploads/${img.filename}" onclick="window.open(this.src)">
                            <div class="image-info">🎨 XỊT SƠN<br>${img.time}</div>
                        </div>
                    `;
                }
                for (const img of data.burglary) {
                    html += `
                        <div class="image-item">
                            <img src="/uploads/${img.filename}" onclick="window.open(this.src)">
                            <div class="image-info">🏠 TRỘM NHÀ<br>${img.time}</div>
                        </div>
                    `;
                }
                imagesDiv.innerHTML = html || '<div style="color:#888; text-align:center;">Chưa có ảnh nào</div>';
            }
            
            function loadAllImages() {
                const grid = document.getElementById('all-images-grid');
                let html = '';
                for (const img of allImages) {
                    html += `
                        <div class="image-item">
                            <img src="/uploads/${img.filename}" onclick="window.open(this.src)">
                            <div class="image-info">👤 ${img.user.toUpperCase()}<br>${img.type === 'graffiti' ? '🎨 XỊT SƠN' : '🏠 TRỘM NHÀ'}<br>${img.time}</div>
                        </div>
                    `;
                }
                grid.innerHTML = html || '<div style="color:#888; text-align:center;">Chưa có ảnh nào</div>';
            }
        </script>
    </body>
    </html>
    ''', users=[u for u in users_db.keys() if u != 'shadowcartel'], 
         users_data={
             u: {
                 "graffiti_count": user_stats.get(u, {}).get("graffiti", 0),
                 "burglary_count": user_stats.get(u, {}).get("burglary", 0),
                 "graffiti": user_images.get(u, {}).get("graffiti", []),
                 "burglary": user_images.get(u, {}).get("burglary", [])
             } for u in users_db.keys() if u != 'shadowcartel'
         },
         all_images=[
             {"user": u, "type": t, "filename": img["filename"], "time": img["time"]}
             for u in users_db.keys() if u != 'shadowcartel'
             for t in ["graffiti", "burglary"]
             for img in user_images.get(u, {}).get(t, [])
         ])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_BASE, filename))

@app.route('/reset_all', methods=['POST'])
@admin_required
def reset_all():
    for user in user_stats:
        if user != 'shadowcartel':
            user_stats[user] = {"graffiti": 0, "burglary": 0}
            user_images[user] = {"graffiti": [], "burglary": []}
    
    # Xóa file ảnh
    for f in os.listdir(UPLOAD_BASE):
        os.remove(os.path.join(UPLOAD_BASE, f))
    
    flash('Đã reset toàn bộ dữ liệu!', 'success')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất!', 'success')
    return redirect(url_for('login'))

@app.route('/bg_image')
def bg_image():
    if os.path.exists(BACKGROUND_IMAGE):
        return send_file(BACKGROUND_IMAGE, mimetype='image/png')
    return "Not Found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
