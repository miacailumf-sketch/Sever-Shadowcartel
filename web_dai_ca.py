from flask import Flask, render_template_string, request, redirect, url_for, send_file, session
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'SHADOW_CARTEL_PREMIUM_2026'

# --- CẤU HÌNH ---
UPLOAD_BASE = 'shadow_data'
BACKGROUND_IMAGE = 'image_6.png'
os.makedirs(UPLOAD_BASE, exist_ok=True)

# DATABASE (Admin mới theo lệnh Đại ca)
users_db = {"shadowcartel": "shadowcartel1012"}
user_stats = {"shadowcartel": 0} 
PRICE_PER_IMAGE = 5000 

# --- GIAO DIỆN PREMIUM GLOW (ĐEN - TRẮNG - ÁNH SÁNG) ---
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    :root { 
        --primary: #ffffff; 
        --glow: rgba(255, 255, 255, 0.6);
        --bg: rgba(0, 0, 0, 0.9);
    }

    body { 
        background: #000 url('/bg_image') no-repeat center center fixed; 
        background-size: cover; color: white; 
        font-family: 'Inter', sans-serif; 
        display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0;
    }

    /* Hiệu ứng mờ ảo cao cấp */
    .glass { 
        background: var(--bg); 
        backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
        border: 1px solid rgba(255, 255, 255, 0.15); 
        border-radius: 24px; padding: 50px; 
        text-align: center; width: 400px; 
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 15px rgba(255, 255, 255, 0.05);
    }

    /* Chữ phát sáng */
    .brand { 
        font-size: 2.2rem; font-weight: 900; letter-spacing: 8px; 
        color: white; text-shadow: 0 0 10px var(--glow), 0 0 20px var(--glow);
        margin-bottom: 10px; text-transform: uppercase;
    }

    .sub-brand { font-size: 0.7rem; letter-spacing: 3px; color: #888; margin-bottom: 30px; }

    /* Input & Button chuyên nghiệp */
    input { 
        background: rgba(255, 255, 255, 0.05); border: 1px solid #333; 
        padding: 16px; color: white; margin: 12px 0; border-radius: 12px; 
        width: 100%; box-sizing: border-box; outline: none; transition: 0.3s;
    }
    input:focus { border-color: white; box-shadow: 0 0 10px var(--glow); }

    button { 
        background: white; color: black; border: none; padding: 16px; 
        font-weight: 800; cursor: pointer; border-radius: 12px; 
        width: 100%; margin-top: 20px; text-transform: uppercase; 
        transition: 0.4s; box-shadow: 0 0 5px var(--glow);
    }
    button:hover { transform: scale(1.02); box-shadow: 0 0 20px white; cursor: pointer; }

    /* Hộp nhiệm vụ có viền sáng */
    .mission-box { 
        flex: 1; padding: 45px 20px; background: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; 
        cursor: pointer; transition: 0.5s; text-align: center;
    }
    .mission-box:hover { 
        background: rgba(255, 255, 255, 0.08); border-color: white;
        transform: translateY(-10px); box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 15px var(--glow);
    }

    table { width: 100%; border-collapse: collapse; margin-top: 30px; }
    th { color: #555; font-size: 0.7rem; text-transform: uppercase; padding-bottom: 10px; border-bottom: 1px solid #222; }
    td { padding: 20px 10px; border-bottom: 1px solid #111; font-weight: 500; }

    .money { color: #00ff88; text-shadow: 0 0 5px rgba(0,255,136,0.3); }

    .logout-link { color: #444; text-decoration: none; font-size: 0.75rem; transition: 0.3s; font-weight: bold; }
    .logout-link:hover { color: white; text-shadow: 0 0 5px white; }
</style>
"""

# --- LOGIC ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        if u in users_db and users_db[u] == p:
            session['user'] = u
            return redirect(url_for('admin' if u == 'shadowcartel' else 'dashboard'))
    return render_template_string(STYLE + """
    <div class="glass">
        <div class="brand">SHADOW CARTEL</div>
        <div class="sub-brand">GIAO THỨC TRUY CẬP</div>
        <form method="post">
            <input name="u" placeholder="TÊN ĐĂNG NHẬP" required autocomplete="off">
            <input name="p" type="password" placeholder="MẬT KHẨU" required>
            <button type="submit">XÁC THỰC</button>
        </form>
        <div style="margin-top:25px;"><a href="/register" class="logout-link">YÊU CẦU CẤP TÀI KHOẢN</a></div>
    </div>
    """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        if u and u not in users_db:
            users_db[u], user_stats[u] = p, 0
            session['user'] = u
            return redirect(url_for('dashboard'))
    return render_template_string(STYLE + """
    <div class="glass">
        <div class="brand">GIA NHẬP</div>
        <div class="sub-brand">HỢP ĐỒNG ĐỆ TỬ</div>
        <form method="post">
            <input name="u" placeholder="TÊN ĐỆ TỬ MỚI" required autocomplete="off">
            <input name="p" type="password" placeholder="MẬT KHẨU BẢO MẬT" required>
            <button type="submit">KÝ TÊN</button>
        </form>
    </div>
    """)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    count = user_stats.get(session['user'], 0)
    return render_template_string(STYLE + f"""
    <div id="main-hub">
        <div class="brand" style="text-align:center; display:block;">SHADOW CARTEL</div>
        <p style="text-align:center; color:#666; font-size:0.8rem;">CHÀO MỪNG: {session['user'].upper()}</p>
        <div class="box-container" style="display:flex; gap:25px; width:700px;">
            <div class="mission-box" onclick="go('ARTILLERY - XỊT SƠN')">
                <h2 style="margin:0;">🎨</h2><h3>XỊT SƠN</h3>
            </div>
            <div class="mission-box" onclick="go('INFILTRATION - TRỘM NHÀ')">
                <h2 style="margin:0;">🏠</h2><h3>TRỘM NHÀ</h3>
            </div>
        </div>
        <div style="text-align:center; margin-top:40px;"><a href="/logout" class="logout-link">[ NGẮT KẾT NỐI ]</a></div>
    </div>
    
    <div id="work-ui" style="display:none; width:700px;" class="glass">
        <h2 id="task-title" class="brand" style="font-size:1.5rem;"></h2>
        <div style="display:flex; gap:20px; margin-top:30px;">
            <div style="flex:1; border:1px solid #333; border-radius:15px; padding:20px;">
                <p style="font-size:0.7rem; color:#444;">CHIẾN TÍCH</p>
                <h2 style="font-size:4rem; margin:0;">{count}</h2>
            </div>
            <div style="flex:2; border:2px dashed #222; border-radius:15px; position:relative; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                <p style="color:#333; font-weight:bold;">TẢI INTEL LÊN</p>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" multiple onchange="this.form.submit()" style="position:absolute; width:100%; height:100%; opacity:0; cursor:pointer;">
                </form>
            </div>
        </div>
        <br><button onclick="location.reload()" style="background:none; border:1px solid #222; color:#333; width:auto; padding:5px 30px; font-size:0.7rem;">TRỞ VỀ HQ</button>
    </div>
    <script>function go(t){{document.getElementById('main-hub').style.display='none';document.getElementById('work-ui').style.display='block';document.getElementById('task-title').innerText=t;}}</script>
    """)

@app.route('/admin')
def admin():
    if session.get('user') != 'shadowcartel': return "TRUY CẬP BỊ TỪ CHỐI", 403
    return render_template_string(STYLE + """
    <div class="glass" style="width:800px;">
        <div class="brand">BẢNG THANH TOÁN</div>
        <table>
            <tr><th>ĐỆ TỬ</th><th>SỐ ẢNH</th><th>TIỀN LƯƠNG</th></tr>
            {% for u, c in stats.items() %}
            {% if u != 'shadowcartel' %}
            <tr>
                <td>{{ u|upper }}</td>
                <td style="font-weight:bold;">{{ c }}</td>
                <td class="money">{{ "{:,.0f}".format(c * price) }} VNĐ</td>
            </tr>
            {% endif %}
            {% endfor %}
        </table>
        <div style="display:flex; gap:20px; margin-top:30px;">
            <form action="/reset" method="post" style="flex:1;"><button type="submit" style="background:#ff4757; color:white; box-shadow: 0 0 10px rgba(255,71,87,0.4);">RESET CUỐI TUẦN</button></form>
            <a href="/logout" style="flex:1;"><button style="background:#111; color:white;">ĐĂNG XUẤT ADMIN</button></a>
        </div>
    </div>
    """, stats=user_stats, price=PRICE_PER_IMAGE)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session: return redirect(url_for('login'))
    files = request.files.getlist('file')
    for f in files:
        if f.filename: user_stats[session['user']] += 1
    return redirect(url_for('dashboard'))

@app.route('/reset', methods=['POST'])
def reset():
    if session.get('user') == 'shadowcartel':
        for u in user_stats: user_stats[u] = 0
    return redirect(url_for('admin'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/bg_image')
def bg_image(): return send_file(BACKGROUND_IMAGE, mimetype='image/png') if os.path.exists(BACKGROUND_IMAGE) else ("Not Found", 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)