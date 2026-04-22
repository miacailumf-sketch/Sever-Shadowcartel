from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, flash, jsonify
import os
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'SHADOW_CARTEL_GTA5VN_2026_SECRET'
app.permanent_session_lifetime = timedelta(days=7)

# ==================== CẤU HÌNH ====================
UPLOAD_BASE = 'shadow_data'
BACKGROUND_IMAGE = 'image_6.png'
os.makedirs(UPLOAD_BASE, exist_ok=True)

# Database
users_db = {
    "shadowcartel": {
        "password": hashlib.sha256("shadowcartel1012".encode()).hexdigest(),
        "role": "admin",
        "joined": datetime.now().strftime("%Y-%m-%d"),
        "total_money": 0,
        "total_missions": 0
    }
}

user_stats = {"shadowcartel": 0}  # Số nhiệm vụ đã làm
user_money = {"shadowcartel": 0}   # Số tiền đã kiếm

# Danh sách nhiệm vụ
MISSIONS = {
    "graffiti": {
        "name": "🎨 XỊT SƠN",
        "description": "Xịt sơn biểu tượng băng đảng lên tường đối thủ",
        "base_reward": 5000,
        "exp": 1,
        "locations": ["Bãi biển Vespucci", "Khu công nghiệp La Mesa", "Hầm chứa metro", "Cầu La Puerta"]
    },
    "burglary": {
        "name": "🏠 TRỘM NHÀ",
        "description": "Đột nhập nhà dân, lấy cắp tài sản giá trị",
        "base_reward": 10000,
        "exp": 2,
        "locations": ["Rockford Hills", "Mirror Park", "Chumash", "Paleto Bay"]
    },
    "heist": {
        "name": "💎 CƯỚP CÓC",
        "description": "Tấn công xe chở tiền, cướp ngân hàng",
        "base_reward": 25000,
        "exp": 5,
        "locations": ["Fleeca Bank", "Pacific Bank", "Xe chở vàng", "Kho bạc"]
    },
    "assassination": {
        "name": "⚔️ THANH TRỪ",
        "description": "Tiêu diệt mục tiêu theo hợp đồng đen",
        "base_reward": 50000,
        "exp": 10,
        "locations": ["Núi Chiliad", "Sân bay quốc tế", "Khu ổ chuột", "Biệt thự tỷ phú"]
    }
}

# Bảng xếp hạng rank
RANKS = [
    {"name": "TẬP SỰ", "min_exp": 0, "color": "#888888"},
    {"name": "ĐỆ TỬ", "min_exp": 10, "color": "#00aa00"},
    {"name": "SÁT THỦ", "min_exp": 30, "color": "#00ccff"},
    {"name": "TRÙM BĂNG", "min_exp": 70, "color": "#ffaa00"},
    {"name": "HUYỀN THOẠI", "min_exp": 150, "color": "#ff00ff"},
    {"name": "SHADOW KING", "min_exp": 300, "color": "#ff4444"}
]

def get_rank(exp):
    for rank in reversed(RANKS):
        if exp >= rank["min_exp"]:
            return rank
    return RANKS[0]

# ==================== GIAO DIỆN CSS ====================
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800;14..32,900&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        background: #000000 url('/bg_image') no-repeat center center fixed;
        background-size: cover;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    
    /* Glassmorphism Effect */
    .glass {
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 28px;
        padding: 40px;
        width: 100%;
        max-width: 900px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
    }
    
    /* Typography - Không in đậm quá mức */
    .brand {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 6px;
        background: linear-gradient(135deg, #ffffff 0%, #aaaaaa 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
        margin-bottom: 8px;
        text-align: center;
    }
    
    .sub-brand {
        font-size: 0.7rem;
        letter-spacing: 3px;
        color: #666666;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 400;
    }
    
    /* Form Elements */
    input, select {
        width: 100%;
        padding: 14px 18px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #333333;
        border-radius: 14px;
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 400;
        outline: none;
        transition: all 0.3s ease;
        margin-bottom: 15px;
        font-family: 'Inter', sans-serif;
    }
    
    input:focus {
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
    }
    
    button {
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
        border: none;
        border-radius: 14px;
        color: #000000;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 10px;
        font-family: 'Inter', sans-serif;
    }
    
    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    /* Mission Cards */
    .mission-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        margin: 30px 0;
    }
    
    .mission-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 25px 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .mission-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-5px);
    }
    
    .mission-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }
    
    .mission-name {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #ffffff;
    }
    
    .mission-reward {
        font-size: 0.8rem;
        color: #00ff88;
        font-weight: 500;
    }
    
    /* Stats Panel */
    .stats-panel {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-around;
        text-align: center;
    }
    
    .stat-item {
        flex: 1;
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffaa00;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: #888888;
        letter-spacing: 1px;
        margin-top: 5px;
        font-weight: 400;
    }
    
    /* Rank Badge */
    .rank-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    /* Table */
    .leaderboard-table {
        width: 100%;
        margin-top: 20px;
        border-collapse: collapse;
    }
    
    .leaderboard-table th {
        text-align: left;
        padding: 12px 8px;
        color: #666666;
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 1px;
        border-bottom: 1px solid #222222;
    }
    
    .leaderboard-table td {
        padding: 12px 8px;
        color: #cccccc;
        font-size: 0.85rem;
        font-weight: 400;
        border-bottom: 1px solid #111111;
    }
    
    /* Flash Messages */
    .flash-success {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
        color: #00ff88;
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 20px;
        font-size: 0.85rem;
        text-align: center;
    }
    
    .flash-error {
        background: rgba(255, 68, 68, 0.1);
        border: 1px solid #ff4444;
        color: #ff4444;
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 20px;
        font-size: 0.85rem;
        text-align: center;
    }
    
    /* Location Selector */
    .location-selector {
        margin: 20px 0;
        padding: 15px;
        background: rgba(0, 0, 0, 0.5);
        border-radius: 16px;
    }
    
    .location-title {
        font-size: 0.8rem;
        color: #888888;
        margin-bottom: 10px;
        font-weight: 400;
    }
    
    .location-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .location-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #333333;
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .location-btn:hover, .location-btn.selected {
        background: rgba(255, 255, 255, 0.15);
        border-color: #ffffff;
    }
    
    /* Back Button */
    .back-btn {
        background: none;
        border: 1px solid #333333;
        color: #888888;
        margin-top: 20px;
        font-weight: 500;
    }
    
    .back-btn:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        transform: none;
        box-shadow: none;
    }
    
    /* Logout Link */
    .logout-link {
        display: block;
        text-align: center;
        margin-top: 25px;
        color: #555555;
        text-decoration: none;
        font-size: 0.7rem;
        transition: color 0.3s;
    }
    
    .logout-link:hover {
        color: #ffffff;
    }
    
    /* Responsive */
    @media (max-width: 700px) {
        .glass { padding: 25px; }
        .mission-grid { grid-template-columns: 1fr; }
        .brand { font-size: 1.8rem; letter-spacing: 3px; }
        .stats-panel { flex-direction: column; gap: 15px; }
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
        
        if username in users_db:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if users_db[username]['password'] == hashed:
                session.permanent = True
                session['user'] = username
                flash(f'Chào mừng {username.upper()} trở lại!', 'success')
                return redirect(url_for('admin' if username == 'shadowcartel' else 'dashboard'))
        
        flash('Sai tên đăng nhập hoặc mật khẩu!', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SHADOW CARTEL | Đăng Nhập</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ''' + STYLE + '''
    </head>
    <body>
        <div class="glass">
            <div class="brand">SHADOW CARTEL</div>
            <div class="sub-brand">GIAO THỨC TRUY CẬP</div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            
            <form method="post">
                <input type="text" name="username" placeholder="TÊN ĐĂNG NHẬP" required autocomplete="off">
                <input type="password" name="password" placeholder="MẬT KHẨU" required>
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
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
        elif username in users_db:
            flash('Tên đăng nhập đã tồn tại!', 'error')
        elif len(password) < 4:
            flash('Mật khẩu phải có ít nhất 4 ký tự!', 'error')
        else:
            users_db[username] = {
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "role": "member",
                "joined": datetime.now().strftime("%Y-%m-%d"),
                "total_money": 0,
                "total_missions": 0
            }
            user_stats[username] = 0
            user_money[username] = 0
            session['user'] = username
            flash(f'Đăng ký thành công! Chào mừng {username.upper()} gia nhập Shadow Cartel!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SHADOW CARTEL | Đăng Ký</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ''' + STYLE + '''
    </head>
    <body>
        <div class="glass">
            <div class="brand">GIA NHẬP</div>
            <div class="sub-brand">HỢP ĐỒNG ĐỆ TỬ</div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            
            <form method="post">
                <input type="text" name="username" placeholder="TÊN ĐỆ TỬ MỚI" required autocomplete="off">
                <input type="password" name="password" placeholder="MẬT KHẨU BẢO MẬT" required>
                <button type="submit">KÝ TÊN</button>
            </form>
            
            <a href="{{ url_for('login') }}" class="logout-link">← QUAY LẠI ĐĂNG NHẬP</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    username = session['user']
    exp = user_stats.get(username, 0)
    money = user_money.get(username, 0)
    rank = get_rank(exp)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SHADOW CARTEL | Bảng Điều Khiển</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ''' + STYLE + '''
    </head>
    <body>
        <div class="glass">
            <div class="brand">SHADOW CARTEL</div>
            <div class="sub-brand">CHÀO MỪNG: {{ username.upper() }}</div>
            
            <div class="stats-panel">
                <div class="stat-item">
                    <div class="stat-value">{{ exp }}</div>
                    <div class="stat-label">KINH NGHIỆM</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ "{:,.0f}".format(money) }}đ</div>
                    <div class="stat-label">TIỀN THƯỞNG</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {{ rank.color }}">{{ rank.name }}</div>
                    <div class="stat-label">CẤP BẬC</div>
                </div>
            </div>
            
            <div class="mission-grid">
                <div class="mission-card" onclick="selectMission('graffiti')">
                    <div class="mission-icon">🎨</div>
                    <div class="mission-name">XỊT SƠN</div>
                    <div class="mission-reward">+5.000đ | +1 EXP</div>
                    <div style="font-size:0.65rem; color:#666; margin-top:8px;">Xịt sơn biểu tượng lên tường đối thủ</div>
                </div>
                <div class="mission-card" onclick="selectMission('burglary')">
                    <div class="mission-icon">🏠</div>
                    <div class="mission-name">TRỘM NHÀ</div>
                    <div class="mission-reward">+10.000đ | +2 EXP</div>
                    <div style="font-size:0.65rem; color:#666; margin-top:8px;">Đột nhập nhà dân, lấy cắp tài sản</div>
                </div>
                <div class="mission-card" onclick="selectMission('heist')">
                    <div class="mission-icon">💎</div>
                    <div class="mission-name">CƯỚP CÓC</div>
                    <div class="mission-reward">+25.000đ | +5 EXP</div>
                    <div style="font-size:0.65rem; color:#666; margin-top:8px;">Tấn công xe chở tiền, cướp ngân hàng</div>
                </div>
                <div class="mission-card" onclick="selectMission('assassination')">
                    <div class="mission-icon">⚔️</div>
                    <div class="mission-name">THANH TRỪ</div>
                    <div class="mission-reward">+50.000đ | +10 EXP</div>
                    <div style="font-size:0.65rem; color:#666; margin-top:8px;">Tiêu diệt mục tiêu theo hợp đồng đen</div>
                </div>
            </div>
            
            <div id="mission-panel" style="display:none;">
                <div style="border-top: 1px solid #222; margin: 20px 0;"></div>
                <h3 id="selected-mission-name" style="text-align:center; margin-bottom:15px;"></h3>
                
                <div class="location-selector">
                    <div class="location-title">📍 CHỌN ĐỊA ĐIỂM THỰC HIỆN</div>
                    <div class="location-buttons" id="location-buttons"></div>
                </div>
                
                <button id="execute-btn" onclick="executeMission()">THỰC HIỆN NHIỆM VỤ</button>
                <button class="back-btn" onclick="cancelMission()">← QUAY LẠI</button>
            </div>
            
            <div id="result-panel" style="display:none;">
                <div style="border-top: 1px solid #222; margin: 20px 0;"></div>
                <div id="result-content" style="text-align:center;"></div>
                <button class="back-btn" onclick="continueMission()">TIẾP TỤC</button>
            </div>
            
            <a href="{{ url_for('leaderboard') }}" class="logout-link">🏆 BẢNG XẾP HẠNG</a>
            <a href="{{ url_for('logout') }}" class="logout-link">[ NGẮT KẾT NỐI ]</a>
        </div>
        
        <script>
            let currentMission = null;
            let currentLocations = [];
            let selectedLocation = null;
            
            function selectMission(missionId) {
                currentMission = missionId;
                const missions = {
                    graffiti: { name: '🎨 XỊT SƠN', locations: {{ MISSIONS.graffiti.locations|tojson }} },
                    burglary: { name: '🏠 TRỘM NHÀ', locations: {{ MISSIONS.burglary.locations|tojson }} },
                    heist: { name: '💎 CƯỚP CÓC', locations: {{ MISSIONS.heist.locations|tojson }} },
                    assassination: { name: '⚔️ THANH TRỪ', locations: {{ MISSIONS.assassination.locations|tojson }} }
                };
                
                currentLocations = missions[missionId].locations;
                document.getElementById('selected-mission-name').innerHTML = missions[missionId].name;
                
                const locationDiv = document.getElementById('location-buttons');
                locationDiv.innerHTML = '';
                currentLocations.forEach((loc, idx) => {
                    const btn = document.createElement('div');
                    btn.className = 'location-btn';
                    btn.innerHTML = loc;
                    btn.onclick = (function(l) {
                        return function() {
                            document.querySelectorAll('.location-btn').forEach(b => b.classList.remove('selected'));
                            this.classList.add('selected');
                            selectedLocation = l;
                        };
                    })(loc);
                    locationDiv.appendChild(btn);
                });
                
                document.querySelector('.mission-grid').style.display = 'none';
                document.getElementById('mission-panel').style.display = 'block';
            }
            
            function executeMission() {
                if (!selectedLocation) {
                    alert('Vui lòng chọn địa điểm thực hiện!');
                    return;
                }
                
                fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'mission=' + encodeURIComponent(currentMission) + '&location=' + encodeURIComponent(selectedLocation)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('result-content').innerHTML = `
                            <div style="font-size:3rem; margin-bottom:15px;">✅</div>
                            <div style="font-size:1.2rem; font-weight:700; margin-bottom:10px;">NHIỆM VỤ HOÀN THÀNH!</div>
                            <div style="color:#aaa; margin-bottom:15px;">Địa điểm: ${data.location}</div>
                            <div style="color:#00ff88; font-size:1.1rem;">+${data.reward.toLocaleString()}đ | +${data.exp} EXP</div>
                        `;
                    } else {
                        document.getElementById('result-content').innerHTML = `
                            <div style="font-size:3rem; margin-bottom:15px;">💀</div>
                            <div style="font-size:1.2rem; font-weight:700; margin-bottom:10px;">THẤT BẠI!</div>
                            <div style="color:#ff4444;">${data.message}</div>
                        `;
                    }
                    
                    document.getElementById('mission-panel').style.display = 'none';
                    document.getElementById('result-panel').style.display = 'block';
                    
                    // Cập nhật số liệu trên UI
                    document.querySelector('.stat-value').innerHTML = data.new_exp || '0';
                    document.querySelectorAll('.stat-value')[1].innerHTML = (data.new_money || 0).toLocaleString() + 'đ';
                });
            }
            
            function cancelMission() {
                currentMission = null;
                selectedLocation = null;
                document.querySelector('.mission-grid').style.display = 'grid';
                document.getElementById('mission-panel').style.display = 'none';
            }
            
            function continueMission() {
                currentMission = null;
                selectedLocation = null;
                document.getElementById('result-panel').style.display = 'none';
                document.querySelector('.mission-grid').style.display = 'grid';
                location.reload();
            }
        </script>
    </body>
    </html>
    ''', username=username, exp=exp, money=money, rank=rank, MISSIONS=MISSIONS)

@app.route('/execute', methods=['POST'])
def execute_mission():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"})
    
    username = session['user']
    mission_id = request.form.get('mission')
    location = request.form.get('location')
    
    if mission_id not in MISSIONS:
        return jsonify({"success": False, "message": "Nhiệm vụ không hợp lệ"})
    
    mission = MISSIONS[mission_id]
    reward = mission["base_reward"]
    exp = mission["exp"]
    
    # Cập nhật
    user_stats[username] = user_stats.get(username, 0) + exp
    user_money[username] = user_money.get(username, 0) + reward
    
    if username != 'shadowcartel':
        user_stats['shadowcartel'] = user_stats.get('shadowcartel', 0) + exp
    
    return jsonify({
        "success": True,
        "reward": reward,
        "exp": exp,
        "location": location,
        "new_exp": user_stats[username],
        "new_money": user_money[username]
    })

@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Tạo bảng xếp hạng
    leaderboard_data = []
    for user in user_stats:
        if user != 'shadowcartel':
            leaderboard_data.append({
                "name": user.upper(),
                "exp": user_stats[user],
                "money": user_money.get(user, 0),
                "rank": get_rank(user_stats[user])
            })
    
    leaderboard_data.sort(key=lambda x: x["exp"], reverse=True)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SHADOW CARTEL | Bảng Xếp Hạng</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ''' + STYLE + '''
    </head>
    <body>
        <div class="glass">
            <div class="brand">🏆 BẢNG XẾP HẠNG</div>
            <div class="sub-brand">THỨ HẠNG ĐỆ TỬ</div>
            
            <table class="leaderboard-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>ĐỆ TỬ</th>
                        <th>CẤP BẬC</th>
                        <th>KINH NGHIỆM</th>
                        <th>TIỀN THƯỞNG</th>
                    </tr>
                </thead>
                <tbody>
                    {% for member in leaderboard %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ member.name }}</td>
                        <td><span class="rank-badge" style="background:{{ member.rank.color }}20; color:{{ member.rank.color }};">{{ member.rank.name }}</span></td>
                        <td>{{ member.exp }}</td>
                        <td style="color:#00ff88;">{{ "{:,.0f}".format(member.money) }}đ</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <a href="{{ url_for('dashboard') }}" class="logout-link">← QUAY LẠI BẢNG ĐIỀU KHIỂN</a>
            <a href="{{ url_for('logout') }}" class="logout-link">[ NGẮT KẾT NỐI ]</a>
        </div>
    </body>
    </html>
    ''', leaderboard=leaderboard_data)

@app.route('/admin')
def admin():
    if session.get('user') != 'shadowcartel':
        flash('Truy cập bị từ chối!', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SHADOW CARTEL | Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ''' + STYLE + '''
    </head>
    <body>
        <div class="glass" style="max-width: 1000px;">
            <div class="brand">👑 BẢNG ĐIỀU HÀNH</div>
            <div class="sub-brand">QUẢN LÝ ĐỆ TỬ SHADOW CARTEL</div>
            
            <table class="leaderboard-table">
                <thead>
                    <tr>
                        <th>ĐỆ TỬ</th>
                        <th>NGÀY GIA NHẬP</th>
                        <th>KINH NGHIỆM</th>
                        <th>TIỀN THƯỞNG</th>
                        <th>CẤP BẬC</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user, info in users.items() %}
                    <tr>
                        <td>{{ user.upper() }}</td>
                        <td>{{ info.joined }}</td>
                        <td>{{ stats.get(user, 0) }}</td>
                        <td style="color:#00ff88;">{{ "{:,.0f}".format(money.get(user, 0)) }}đ</td>
                        <td><span class="rank-badge" style="background:{{ rank.color }}20; color:{{ rank.color }};">{{ rank.name }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div style="display: flex; gap: 15px; margin-top: 25px;">
                <form action="/reset" method="post" style="flex:1;">
                    <button type="submit" style="background: #ff4444; color: white;">🔄 RESET TUẦN MỚI</button>
                </form>
                <a href="{{ url_for('dashboard') }}" style="flex:1;">
                    <button style="background: #333; color: white;">← VỀ BẢNG ĐIỀU KHIỂN</button>
                </a>
            </div>
            
            <a href="{{ url_for('logout') }}" class="logout-link">[ ĐĂNG XUẤT ]</a>
        </div>
    </body>
    </html>
    ''', users=users_db, stats=user_stats, money=user_money, rank=get_rank(0))

@app.route('/reset', methods=['POST'])
def reset():
    if session.get('user') != 'shadowcartel':
        return redirect(url_for('dashboard'))
    
    for user in user_stats:
        if user != 'shadowcartel':
            user_stats[user] = 0
            user_money[user] = 0
    
    flash('Đã reset dữ liệu tuần mới!', 'success')
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
