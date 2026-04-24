from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, flash, jsonify
import os
import hashlib
from datetime import datetime
from functools import wraps
import uuid
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'SHADOW_CARTEL_GTA5VN_2026_SECRET'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# ==================== CẤU HÌNH MONGODB (BẤT TỬ) ====================
MONGO_URI = "mongodb+srv://miacailumf_db_user:xWK1sQ9NACSJjNZy@cluster0.8udfc8t.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['ShadowCartel_Upload_DB']
users_col = db['users']
# Lưu ý: Database này sẽ lưu thông tin user, số lượng ảnh (stats) và danh sách file ảnh (images)

UPLOAD_BASE = 'shadow_uploads'
BACKGROUND_IMAGE = 'image_7.png' # Đã đổi thành 7 cho Đại ca phong thủy
os.makedirs(UPLOAD_BASE, exist_ok=True)

# Khởi tạo Admin nếu chưa có
def init_admin():
    admin = users_col.find_one({"username": "shadowcartel"})
    if not admin:
        users_col.insert_one({
            "username": "shadowcartel",
            "password": hashlib.sha256("shadowcartel1012".encode()).hexdigest(),
            "role": "admin",
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "stats": {"graffiti": 0, "burglary": 0},
            "images": {"graffiti": [], "burglary": []}
        })

init_admin()

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

# ==================== GIAO DIỆN CSS (GIỮ NGUYÊN) ====================
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #000000 url('/bg_image') no-repeat center center fixed; background-size: cover; font-family: 'Inter', sans-serif; min-height: 100vh; padding: 20px; }
    .glass { background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 28px; padding: 30px; max-width: 1200px; margin: 0 auto; }
    .brand { font-size: 2.2rem; font-weight: 800; letter-spacing: 4px; background: linear-gradient(135deg, #ffffff 0%, #888888 100%); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; margin-bottom: 8px; }
    .sub-brand { font-size: 0.7rem; letter-spacing: 2px; color: #666; text-align: center; margin-bottom: 30px; }
    .missions-container { display: flex; gap: 30px; flex-wrap: wrap; }
    .mission-card { flex: 1; min-width: 300px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 25px; }
    .mission-header { text-align: center; padding-bottom: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; }
    .mission-icon { font-size: 3rem; margin-bottom: 10px; }
    .mission-title { font-size: 1.5rem; font-weight: 700; letter-spacing: 2px; }
    .stats-panel { background: rgba(0, 0, 0, 0.5); border-radius: 20px; padding: 20px; margin-bottom: 20px; text-align: center; }
    .stats-label { font-size: 0.7rem; color: #888; letter-spacing: 1px; margin-bottom: 8px; }
    .stats-number { font-size: 2.5rem; font-weight: 800; color: #ffaa00; }
    .upload-area { border: 2px dashed rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s; margin-bottom: 20px; }
    .upload-area:hover { border-color: rgba(255, 255, 255, 0.5); background: rgba(255, 255, 255, 0.03); }
    .upload-icon { font-size: 2rem; margin-bottom: 10px; }
    button { width: 100%; padding: 12px; background: #fff; border: none; border-radius: 14px; color: #000; font-weight: 700; cursor: pointer; }
    .logout-link { display: block; text-align: center; margin-top: 30px; color: #555; text-decoration: none; font-size: 0.7rem; }
    .flash-success { background: rgba(0,255,136,0.1); color: #00ff88; padding: 12px; border-radius: 12px; margin-bottom: 20px; text-align: center; }
    .flash-error { background: rgba(255,68,68,0.1); color: #ff4444; padding: 12px; border-radius: 12px; margin-bottom: 20px; text-align: center; }
    .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
    .image-item { background: rgba(0,0,0,0.5); border-radius: 12px; padding: 10px; text-align: center; }
    .image-item img { max-width: 100%; border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
    .admin-tab { background: rgba(255,255,255,0.05); padding: 10px 20px; border-radius: 30px; cursor: pointer; display: inline-block; margin-right: 10px; }
    .admin-tab.active { background: rgba(255,255,255,0.15); border: 1px solid #fff; }
    .user-select { width: 100%; padding: 10px; background: #222; border: 1px solid #444; border-radius: 12px; color: #fff; margin-bottom: 20px; }
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
        password = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
        user = users_col.find_one({"username": username, "password": password})
        if user:
            session.permanent = True
            session['user'] = username
            flash(f'Chào mừng {username.upper()}!', 'success')
            return redirect(url_for('admin' if username == 'shadowcartel' else 'dashboard'))
        flash('Sai tên đăng nhập hoặc mật khẩu!', 'error')
    return render_template_string('''<!DOCTYPE html><html><head><title>Login</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''</head><body><div class="glass" style="max-width:450px;"><div class="brand">SHADOW CARTEL</div><div class="sub-brand">GIAO THỨC TRUY CẬP</div>{% with messages = get_flashed_messages(with_categories=true) %}{% for c, m in messages %}<div class="flash-{{c}}">{{m}}</div>{% endfor %}{% endwith %}<form method="post"><input type="text" name="username" placeholder="TÊN ĐĂNG NHẬP" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;"><input type="password" name="password" placeholder="MẬT KHẨU" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;"><button type="submit">XÁC THỰC</button></form><a href="/register" class="logout-link">ĐĂNG KÝ THÀNH VIÊN MỚI</a></div></body></html>''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        if users_col.find_one({"username": username}):
            flash('Tên đã tồn tại!', 'error')
        else:
            users_col.insert_one({
                "username": username,
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "role": "member",
                "joined": datetime.now().strftime("%Y-%m-%d"),
                "stats": {"graffiti": 0, "burglary": 0},
                "images": {"graffiti": [], "burglary": []}
            })
            session['user'] = username
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('dashboard'))
    return render_template_string('''<!DOCTYPE html><html><head><title>Register</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''</head><body><div class="glass" style="max-width:450px;"><div class="brand">GIA NHẬP</div><div class="sub-brand">HỢP ĐỒNG ĐỆ TỬ</div><form method="post"><input type="text" name="username" placeholder="TÊN ĐỆ TỬ MỚI" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;"><input type="password" name="password" placeholder="MẬT KHẨU" required style="width:100%; padding:14px; margin-bottom:15px; background:rgba(255,255,255,0.05); border:1px solid #333; border-radius:14px; color:#fff;"><button type="submit">KÝ TÊN</button></form><a href="/login" class="logout-link">← QUAY LẠI</a></div></body></html>''')

@app.route('/dashboard')
@login_required
def dashboard():
    user = users_col.find_one({"username": session['user']})
    return render_template_string('''<!DOCTYPE html><html><head><title>Dashboard</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''</head><body><div class="glass"><div class="brand">SHADOW CARTEL</div><div class="sub-brand">CHÀO MỪNG: {{ user.username.upper() }}</div>
    {% with messages = get_flashed_messages(with_categories=true) %}{% for c, m in messages %}<div class="flash-{{c}}">{{m}}</div>{% endfor %}{% endwith %}
    <div class="missions-container">
        <div class="mission-card">
            <div class="mission-header"><div class="mission-icon">🎨</div><div class="mission-title">XỊT SƠN</div></div>
            <div class="stats-panel"><div class="stats-label">SỐ ẢNH ĐÃ GỬI</div><div class="stats-number">{{ user.stats.graffiti }}</div></div>
            <div class="upload-area" onclick="document.getElementById('f-graffiti').click()"><div class="upload-icon">📤</div><div class="upload-text">GỬI ẢNH XỊT SƠN</div></div>
            <form action="/upload" method="post" enctype="multipart/form-data" style="display:none;"><input type="file" name="file" id="f-graffiti" accept="image/*" onchange="this.form.submit()"><input type="hidden" name="type" value="graffiti"></form>
        </div>
        <div class="mission-card">
            <div class="mission-header"><div class="mission-icon">🏠</div><div class="mission-title">TRỘM NHÀ</div></div>
            <div class="stats-panel"><div class="stats-label">SỐ ẢNH ĐÃ GỬI</div><div class="stats-number">{{ user.stats.burglary }}</div></div>
            <div class="upload-area" onclick="document.getElementById('f-burglary').click()"><div class="upload-icon">📤</div><div class="upload-text">GỬI ẢNH TRỘM NHÀ</div></div>
            <form action="/upload" method="post" enctype="multipart/form-data" style="display:none;"><input type="file" name="file" id="f-burglary" accept="image/*" onchange="this.form.submit()"><input type="hidden" name="type" value="burglary"></form>
        </div>
    </div>
    <a href="/logout" class="logout-link">[ NGẮT KẾT NỐI ]</a></div></body></html>''', user=user)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    username = session['user']
    m_type = request.form.get('type')
    if 'file' not in request.files or m_type not in ['graffiti', 'burglary']:
        return redirect('/dashboard')
    
    file = request.files['file']
    if file.filename == '': return redirect('/dashboard')
    
    # Lưu file vật lý để hiển thị
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
    filename = f"{username}_{m_type}_{uuid.uuid4().hex[:6]}.{ext}"
    file.save(os.path.join(UPLOAD_BASE, filename))
    
    # Cập nhật MongoDB
    img_data = {"filename": filename, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    users_col.update_one(
        {"username": username},
        {"$inc": {f"stats.{m_type}": 1}, "$push": {f"images.{m_type}": img_data}}
    )
    
    flash('Đã gửi ảnh thành công!', 'success')
    return redirect('/dashboard')

@app.route('/admin')
@admin_required
def admin():
    users = list(users_col.find({"role": "member"}))
    all_imgs = []
    for u in users:
        for t in ['graffiti', 'burglary']:
            for img in u['images'].get(t, []):
                all_imgs.append({"user": u['username'], "type": t, "filename": img['filename'], "time": img['time']})

    return render_template_string('''<!DOCTYPE html><html><head><title>Admin</title><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + STYLE + '''</head><body><div class="glass"><div class="brand">👑 BẢNG ĐIỀU HÀNH</div>
    <div class="admin-tabs"><div class="admin-tab active" onclick="showTab('users')">👥 ĐỆ TỬ</div><div class="admin-tab" onclick="showTab('imgs')">🖼️ TẤT CẢ ẢNH</div></div>
    
    <div id="tab-users">
        <select id="u-sel" class="user-select" onchange="loadUser(this.value)">
            <option value="">-- CHỌN ĐỆ TỬ --</option>
            {% for u in users %}<option value="{{u.username}}">{{u.username.upper()}}</option>{% endfor %}
        </select>
        <div id="u-display" class="image-grid"></div>
    </div>
    
    <div id="tab-imgs" style="display:none;"><div class="image-grid">
        {% for i in all_imgs %}
        <div class="image-item"><img src="/uploads/{{i.filename}}" onclick="window.open(this.src)"><div style="font-size:0.7rem; color:#888;">{{i.user.upper()}}<br>{{i.time}}</div></div>
        {% endfor %}
    </div></div>
    
    <form action="/reset_all" method="post" style="margin-top:20px;"><button type="submit" style="background:#ff4444; color:#fff;">RESET TOÀN BỘ DỮ LIỆU</button></form>
    <a href="/dashboard" class="logout-link">QUAY LẠI</a></div>
    <script>
        const data = {{ users|tojson }};
        function showTab(t){
            document.getElementById('tab-users').style.display = t=='users'?'block':'none';
            document.getElementById('tab-imgs').style.display = t=='imgs'?'block':'none';
        }
        function loadUser(un){
            const u = data.find(x => x.username == un);
            let h = '';
            if(u){
                ['graffiti', 'burglary'].forEach(t => {
                    u.images[t].forEach(i => {
                        h += `<div class="image-item"><img src="/uploads/${i.filename}" onclick="window.open(this.src)"><div style="font-size:0.7rem; color:#888;">${t.toUpperCase()}<br>${i.time}</div></div>`;
                    });
                });
            }
            document.getElementById('u-display').innerHTML = h;
        }
    </script></body></html>''', users=users, all_imgs=all_imgs)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_BASE, filename))

@app.route('/reset_all', methods=['POST'])
@admin_required
def reset_all():
    users_col.update_many({"role": "member"}, {"$set": {"stats": {"graffiti": 0, "burglary": 0}, "images": {"graffiti": [], "burglary": []}}})
    for f in os.listdir(UPLOAD_BASE): os.remove(os.path.join(UPLOAD_BASE, f))
    flash('Đã dọn dẹp sạch sẽ!', 'success')
    return redirect('/admin')

@app.route('/bg_image')
def bg_image():
    if os.path.exists(BACKGROUND_IMAGE): return send_file(BACKGROUND_IMAGE)
    return "Not Found", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
