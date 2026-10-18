# ============================================================
# BACKEND: Sistem Pendukung Keputusan (SPK)
# Klasifikasi Kelayakan Penerima Bansos
# ============================================================

from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, send_file
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from decimal import Decimal
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'super_secret_key_bansos'  # Perlu untuk session
app.config['SESSION_TYPE'] = 'filesystem'

# ============================================================
# KONFIGURASI DATABASE
# ============================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'spk_bansos',
    'port': 3306
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ============================================================
# HELPER: Konversi Decimal ke float (untuk JSON serialization)
# ============================================================
def decimal_to_float(obj):
    """Konversi semua Decimal dalam dict/list ke float secara rekursif."""
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_float(val) for key, val in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

# ============================================================
# AUTENTIKASI: Middleware
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Jika request dari API (AJAX), kembalikan JSON 401
            if request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Sesi habis, silakan login kembali'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# HELPER: Ambil Bobot dari Database
# ============================================================
def get_bobot_kriteria():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bobot_kriteria")
        data = cursor.fetchall()
        cursor.close()
        
        bobot = {}
        tipe_kriteria = {}
        for row in data:
            bobot[row['kode_kriteria']] = float(row['bobot'])
            tipe_kriteria[row['kode_kriteria']] = row['tipe']
            
        return bobot, tipe_kriteria
    finally:
        conn.close()

# ============================================================
# FUNGSI UTAMA: PERHITUNGAN SAW
# ============================================================
def hitung_saw(data_penduduk):
    if not data_penduduk:
        return []

    bobot, tipe_kriteria = get_bobot_kriteria()
    kriteria_keys = ['pendapatan', 'luas_lahan', 'jumlah_tanggungan', 'kepadatan_penduduk']

    min_val = {}
    max_val = {}

    for key in kriteria_keys:
        values = [float(d[key]) for d in data_penduduk]
        min_val[key] = min(values)
        max_val[key] = max(values)

    hasil = []

    for penduduk in data_penduduk:
        normalisasi = {}
        for key in kriteria_keys:
            xij = float(penduduk[key])
            
            if tipe_kriteria[key] == 'benefit':
                # Benefit: Rij = Xij / max(Xi)
                if max_val[key] == 0:
                    normalisasi[key] = 0.0
                elif max_val[key] == min_val[key]:
                    # Semua nilai sama → semua mendapat normalisasi 1.0
                    normalisasi[key] = 1.0
                else:
                    normalisasi[key] = xij / max_val[key]
            else:
                # Cost: Rij = min(Xi) / Xij
                if xij == 0:
                    normalisasi[key] = 0.0
                elif max_val[key] == min_val[key]:
                    # Semua nilai sama → semua mendapat normalisasi 1.0
                    normalisasi[key] = 1.0
                else:
                    normalisasi[key] = min_val[key] / xij

        skor_vi = 0.0
        detail_perhitungan = {}

        for key in kriteria_keys:
            kontribusi = bobot[key] * normalisasi[key]
            detail_perhitungan[key] = {
                'nilai_asli': float(penduduk[key]),
                'normalisasi_rij': round(normalisasi[key], 4),
                'bobot_wj': bobot[key],
                'kontribusi_wj_x_rij': round(kontribusi, 4)
            }
            skor_vi += kontribusi

        if skor_vi > 0.8:
            klasifikasi = 'Sangat Layak'
            warna = 'success'
        elif skor_vi >= 0.5:
            klasifikasi = 'Layak'
            warna = 'warning'
        else:
            klasifikasi = 'Tidak Layak'
            warna = 'danger'

        hasil.append({
            'id': penduduk['id'],
            'nama': penduduk['nama'],
            'alamat': penduduk['alamat'],
            'pendapatan': float(penduduk['pendapatan']),
            'jumlah_tanggungan': int(penduduk['jumlah_tanggungan']),
            'luas_lahan': float(penduduk['luas_lahan']),
            'kepadatan_penduduk': float(penduduk['kepadatan_penduduk']),
            'normalisasi': {k: round(v, 4) for k, v in normalisasi.items()},
            'detail_perhitungan': detail_perhitungan,
            'skor': round(skor_vi, 4),
            'klasifikasi': klasifikasi,
            'warna': warna
        })

    hasil.sort(key=lambda x: x['skor'], reverse=True)
    for i, item in enumerate(hasil):
        item['ranking'] = i + 1

    return hasil

# ============================================================
# HALAMAN HTML (ROUTES)
# ============================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return send_from_directory('static', 'login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return send_from_directory('static', 'register.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return send_from_directory('static', 'dashboard.html')

@app.route('/penduduk')
@login_required
def penduduk_page():
    return send_from_directory('static', 'penduduk.html')

@app.route('/bobot')
@login_required
def bobot_page():
    return send_from_directory('static', 'bobot.html')

@app.route('/perhitungan')
@login_required
def perhitungan_page():
    return send_from_directory('static', 'perhitungan.html')

@app.route('/laporan')
@login_required
def laporan_page():
    return send_from_directory('static', 'laporan.html')

# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/session', methods=['GET'])
def api_session():
    """Cek status session untuk frontend."""
    if 'user_id' in session:
        return jsonify({
            'status': 'success',
            'logged_in': True,
            'nama_lengkap': session.get('nama_lengkap', 'User')
        })
    return jsonify({'status': 'success', 'logged_in': False})

@app.route('/api/login', methods=['POST'])
def api_login():
    conn = None
    try:
        body = request.get_json()
        username = body.get('username', '').strip()
        password = body.get('password', '')

        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Username dan password wajib diisi'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['nama_lengkap'] = user['nama_lengkap']
            return jsonify({'status': 'success', 'message': 'Login berhasil'})
        else:
            return jsonify({'status': 'error', 'message': 'Username atau password salah'}), 401

    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'status': 'success'})

@app.route('/api/register', methods=['POST'])
def api_register():
    conn = None
    try:
        body = request.get_json()
        username = body.get('username', '').strip()
        password = body.get('password', '')
        nama_lengkap = body.get('nama_lengkap', '').strip()
        
        if not username or not password or not nama_lengkap:
            return jsonify({'status': 'error', 'message': 'Semua field wajib diisi'}), 400

        if len(password) < 6:
            return jsonify({'status': 'error', 'message': 'Password minimal 6 karakter'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Cek ketersediaan username
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'status': 'error', 'message': 'Username sudah terdaftar'}), 400
            
        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash, nama_lengkap) VALUES (%s, %s, %s)",
                       (username, hashed_pw, nama_lengkap))
        conn.commit()
        cursor.close()
        
        return jsonify({'status': 'success', 'message': 'Akun berhasil didaftarkan'}), 201
        
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Total warga
        cursor.execute("SELECT COUNT(*) as total, AVG(pendapatan) as avg_pendapatan FROM penduduk")
        stats = cursor.fetchone()
        
        # Data untuk perhitungan jumlah layak
        cursor.execute("SELECT * FROM penduduk")
        data = cursor.fetchall()
        cursor.close()

        # Konversi Decimal
        data = decimal_to_float(data)

        hasil = hitung_saw(data) if data else []
        
        sangat_layak = len([h for h in hasil if h['klasifikasi'] == 'Sangat Layak'])
        layak = len([h for h in hasil if h['klasifikasi'] == 'Layak'])
        tidak_layak = len([h for h in hasil if h['klasifikasi'] == 'Tidak Layak'])

        return jsonify({
            'status': 'success',
            'total_warga': stats['total'],
            'avg_pendapatan': float(stats['avg_pendapatan']) if stats['avg_pendapatan'] else 0,
            'klasifikasi': {
                'sangat_layak': sangat_layak,
                'layak': layak,
                'tidak_layak': tidak_layak
            }
        })
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/bobot', methods=['GET'])
@login_required
def api_get_bobot():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bobot_kriteria")
        data = cursor.fetchall()
        cursor.close()
        return jsonify({'status': 'success', 'data': decimal_to_float(data)})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/bobot', methods=['PUT'])
@login_required
def api_update_bobot():
    conn = None
    try:
        body = request.get_json()
        
        if not body or not isinstance(body, dict):
            return jsonify({'status': 'error', 'message': 'Data bobot tidak valid'}), 400

        # Validasi semua nilai harus numerik
        for kode, bobot in body.items():
            try:
                float(bobot)
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': f'Nilai bobot "{kode}" tidak valid'}), 400

        total = sum(float(v) for v in body.values())
        
        # Cek toleransi floating point
        if not (0.99 <= total <= 1.01):
             return jsonify({'status': 'error', 'message': f'Total bobot harus 1.0 (100%). Total saat ini: {total:.2f}'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Validasi: ambil kode kriteria yang valid dari database
        cursor.execute("SELECT kode_kriteria FROM bobot_kriteria")
        valid_codes = {row['kode_kriteria'] for row in cursor.fetchall()}
        
        # Cek apakah semua kode yang dikirim valid
        invalid_codes = set(body.keys()) - valid_codes
        if invalid_codes:
            cursor.close()
            return jsonify({'status': 'error', 'message': f'Kode kriteria tidak valid: {", ".join(invalid_codes)}'}), 400
        
        for kode, bobot in body.items():
            cursor.execute("UPDATE bobot_kriteria SET bobot=%s WHERE kode_kriteria=%s", (float(bobot), kode))
            
        conn.commit()
        cursor.close()
        
        return jsonify({'status': 'success', 'message': 'Bobot berhasil diperbarui'})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/penduduk', methods=['GET'])
@login_required
def get_all_penduduk():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM penduduk ORDER BY id ASC")
        data = cursor.fetchall()
        cursor.close()

        # Konversi Decimal ke float
        data = decimal_to_float(data)

        hasil = hitung_saw(data)
        bobot, tipe_kriteria = get_bobot_kriteria()

        return jsonify({
            'status': 'success',
            'bobot': bobot,
            'tipe_kriteria': tipe_kriteria,
            'total_data': len(hasil),
            'data': hasil,
            'raw_data': data
        })
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/penduduk/<int:id>', methods=['GET'])
@login_required
def get_penduduk_by_id(id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM penduduk WHERE id = %s", (id,))
        data = cursor.fetchone()
        cursor.close()
        if not data:
            return jsonify({'status': 'error', 'message': 'Data tidak ditemukan'}), 404
        return jsonify({'status': 'success', 'data': decimal_to_float(data)})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/penduduk', methods=['POST'])
@login_required
def tambah_penduduk():
    conn = None
    try:
        body = request.get_json()
        required = ['nama', 'alamat', 'pendapatan', 'jumlah_tanggungan', 'luas_lahan', 'kepadatan_penduduk']
        for field in required:
            if field not in body or body[field] == '' or body[field] is None:
                return jsonify({'status': 'error', 'message': f'Field "{field}" wajib diisi'}), 400

        # Validasi nilai numerik
        try:
            pendapatan = float(body['pendapatan'])
            tanggungan = int(body['jumlah_tanggungan'])
            lahan = float(body['luas_lahan'])
            kepadatan = float(body['kepadatan_penduduk'])
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Nilai numerik tidak valid'}), 400

        if pendapatan < 0 or tanggungan < 0 or lahan < 0 or kepadatan < 0:
            return jsonify({'status': 'error', 'message': 'Nilai tidak boleh negatif'}), 400

        nama = str(body['nama']).strip()
        alamat = str(body['alamat']).strip()
        
        if not nama:
            return jsonify({'status': 'error', 'message': 'Nama tidak boleh kosong'}), 400
        if not alamat:
            return jsonify({'status': 'error', 'message': 'Alamat tidak boleh kosong'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Cek duplikat data
        cursor.execute("SELECT id FROM penduduk WHERE LOWER(TRIM(nama)) = LOWER(%s) AND LOWER(TRIM(alamat)) = LOWER(%s)", (nama, alamat))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'status': 'error', 'message': f'Data penduduk dengan nama "{nama}" dan alamat "{alamat}" sudah terdaftar.'}), 400

        sql = """INSERT INTO penduduk 
                 (nama, alamat, pendapatan, jumlah_tanggungan, luas_lahan, kepadatan_penduduk) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (nama, alamat, pendapatan, tanggungan, lahan, kepadatan)
        cursor.execute(sql, values)
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()

        return jsonify({'status': 'success', 'message': f'Data berhasil ditambahkan', 'id': new_id}), 201
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/penduduk/<int:id>', methods=['PUT'])
@login_required
def update_penduduk(id):
    conn = None
    try:
        body = request.get_json()
        
        # Validasi field wajib
        required = ['nama', 'alamat', 'pendapatan', 'jumlah_tanggungan', 'luas_lahan', 'kepadatan_penduduk']
        for field in required:
            if field not in body or body[field] == '' or body[field] is None:
                return jsonify({'status': 'error', 'message': f'Field "{field}" wajib diisi'}), 400

        # Validasi nilai numerik
        try:
            pendapatan = float(body['pendapatan'])
            tanggungan = int(body['jumlah_tanggungan'])
            lahan = float(body['luas_lahan'])
            kepadatan = float(body['kepadatan_penduduk'])
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Nilai numerik tidak valid'}), 400

        if pendapatan < 0 or tanggungan < 0 or lahan < 0 or kepadatan < 0:
            return jsonify({'status': 'error', 'message': 'Nilai tidak boleh negatif'}), 400

        nama = str(body['nama']).strip()
        alamat = str(body['alamat']).strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Cek duplikat data (untuk ID selain ID saat ini)
        cursor.execute("SELECT id FROM penduduk WHERE LOWER(TRIM(nama)) = LOWER(%s) AND LOWER(TRIM(alamat)) = LOWER(%s) AND id != %s", (nama, alamat, id))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'status': 'error', 'message': f'Data penduduk dengan nama "{nama}" dan alamat "{alamat}" sudah terdaftar.'}), 400

        sql = """UPDATE penduduk SET 
                 nama=%s, alamat=%s, pendapatan=%s, 
                 jumlah_tanggungan=%s, luas_lahan=%s, kepadatan_penduduk=%s 
                 WHERE id=%s"""
        values = (nama, alamat, pendapatan, tanggungan, lahan, kepadatan, id)
        cursor.execute(sql, values)
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({'status': 'error', 'message': 'Data tidak ditemukan'}), 404

        cursor.close()
        return jsonify({'status': 'success', 'message': 'Data berhasil diperbarui'})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/penduduk/<int:id>', methods=['DELETE'])
@login_required
def hapus_penduduk(id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM penduduk WHERE id = %s", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({'status': 'error', 'message': 'Data tidak ditemukan'}), 404

        cursor.close()
        return jsonify({'status': 'success', 'message': 'Data berhasil dihapus'})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/perhitungan/<int:id>', methods=['GET'])
@login_required
def detail_perhitungan(id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM penduduk ORDER BY id ASC")
        all_data = cursor.fetchall()
        cursor.close()

        # Konversi Decimal
        all_data = decimal_to_float(all_data)

        hasil = hitung_saw(all_data)
        detail = next((h for h in hasil if h['id'] == id), None)

        if not detail:
            return jsonify({'status': 'error', 'message': 'Data tidak ditemukan'}), 404

        kriteria_keys = ['pendapatan', 'luas_lahan', 'jumlah_tanggungan', 'kepadatan_penduduk']
        min_max = {}
        bobot, tipe_kriteria = get_bobot_kriteria()
        
        for key in kriteria_keys:
            values = [float(d[key]) for d in all_data]
            min_max[key] = {
                'min': min(values),
                'max': max(values),
                'tipe': tipe_kriteria[key]
            }

        return jsonify({'status': 'success', 'min_max_kriteria': min_max, 'data': detail})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if conn:
            conn.close()

# ============================================================
# API IMPORT & TEMPLATE DOWNLOAD
# ============================================================

@app.route('/api/penduduk/template', methods=['GET'])
@login_required
def download_template():
    import io
    import pandas as pd
    
    # Create empty dataframe with template headers
    df = pd.DataFrame(columns=[
        'Nama Lengkap', 
        'Alamat / Desa', 
        'Pendapatan (Rp/bulan)', 
        'Jumlah Tanggungan', 
        'Luas Lahan (m2)', 
        'Kepadatan Penduduk (jiwa/km2)'
    ])
    
    # Add sample rows
    df.loc[0] = ['Slamet Widodo', 'Desa Gudangharjo, RT 01/RW 02', 800000, 5, 50.0, 320.5]
    df.loc[1] = ['Sri Mulyani', 'Desa Paranggupito, RT 03/RW 01', 1200000, 3, 120.0, 280.75]
    
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Penduduk')
    out.seek(0)
    
    return send_file(
        out,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='template_import_penduduk.xlsx'
    )

@app.route('/api/penduduk/import', methods=['POST'])
@login_required
def api_import_penduduk():
    import io
    import pandas as pd
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Tidak ada berkas yang dikirim'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Nama berkas kosong'}), 400
        
    # Dapatkan ekstensi berkas
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['xlsx', 'xls', 'csv']:
        return jsonify({'status': 'error', 'message': 'Format berkas tidak didukung. Gunakan Excel (.xlsx, .xls) atau CSV (.csv)'}), 400
        
    try:
        # Baca berkas
        file_bytes = file.read()
        if ext == 'csv':
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            
        # Bersihkan data: hapus baris yang kosong semua, rapikan nama kolom
        df.dropna(how='all', inplace=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Pemetaan kolom secara dinamis (case-insensitive & kata kunci)
        col_mappings = {
            'nama': None,
            'alamat': None,
            'pendapatan': None,
            'tanggungan': None,
            'lahan': None,
            'kepadatan': None
        }
        
        for col in df.columns:
            col_lower = col.lower()
            if 'nama' in col_lower or 'name' in col_lower:
                col_mappings['nama'] = col
            elif 'alamat' in col_lower or 'desa' in col_lower or 'address' in col_lower:
                col_mappings['alamat'] = col
            elif 'pendapatan' in col_lower or 'gaji' in col_lower or 'income' in col_lower:
                col_mappings['pendapatan'] = col
            elif 'tanggungan' in col_lower or 'anak' in col_lower or 'depend' in col_lower:
                col_mappings['tanggungan'] = col
            elif 'lahan' in col_lower or 'luas' in col_lower or 'land' in col_lower:
                col_mappings['lahan'] = col
            elif 'kepadatan' in col_lower or 'penduduk' in col_lower or 'density' in col_lower:
                col_mappings['kepadatan'] = col
                
        # Periksa kolom yang hilang
        missing = [k for k, v in col_mappings.items() if v is None]
        if missing:
            readable_missing = {
                'nama': 'Nama Lengkap',
                'alamat': 'Alamat / Desa',
                'pendapatan': 'Pendapatan (Rp/bulan)',
                'tanggungan': 'Jumlah Tanggungan',
                'lahan': 'Luas Lahan (m2)',
                'kepadatan': 'Kepadatan Penduduk'
            }
            missing_names = [readable_missing[m] for m in missing]
            return jsonify({
                'status': 'error', 
                'message': f'Kolom berikut tidak ditemukan di file Anda: {", ".join(missing_names)}. Pastikan nama kolom sesuai template.'
            }), 400
            
        # Proses validasi dan input ke database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Mulai transaksi database
        conn.start_transaction()

        # Ambil semua data nama dan alamat yang sudah ada di database untuk pencegahan duplikasi
        cursor.execute("SELECT LOWER(TRIM(nama)), LOWER(TRIM(alamat)) FROM penduduk")
        existing_records = {(row[0], row[1]) for row in cursor.fetchall()}
        seen_in_file = set()
        
        imported_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # baris data pertama di Excel biasanya baris ke-2 (baris 1 adalah header)
            try:
                # Ambil nilai asli dari kolom
                raw_nama = row[col_mappings['nama']]
                raw_alamat = row[col_mappings['alamat']]
                raw_pendapatan = row[col_mappings['pendapatan']]
                raw_tanggungan = row[col_mappings['tanggungan']]
                raw_lahan = row[col_mappings['lahan']]
                raw_kepadatan = row[col_mappings['kepadatan']]
                
                # Validasi field wajib
                if pd.isna(raw_nama) or str(raw_nama).strip() == '':
                    raise ValueError("Nama lengkap tidak boleh kosong")
                if pd.isna(raw_alamat) or str(raw_alamat).strip() == '':
                    raise ValueError("Alamat tidak boleh kosong")
                    
                # Konversi tipe data yang aman
                try:
                    pendapatan = float(raw_pendapatan)
                except:
                    raise ValueError(f"Nilai pendapatan '{raw_pendapatan}' harus berupa angka numerik")
                    
                try:
                    tanggungan = int(raw_tanggungan)
                except:
                    raise ValueError(f"Jumlah tanggungan '{raw_tanggungan}' harus berupa angka bulat")
                    
                try:
                    lahan = float(raw_lahan)
                except:
                    raise ValueError(f"Luas lahan '{raw_lahan}' harus berupa angka numerik")
                    
                try:
                    kepadatan = float(raw_kepadatan)
                except:
                    raise ValueError(f"Kepadatan penduduk '{raw_kepadatan}' harus berupa angka numerik")
                    
                # Validasi nilai tidak boleh negatif
                if pendapatan < 0 or tanggungan < 0 or lahan < 0 or kepadatan < 0:
                    raise ValueError("Nilai tidak boleh negatif")
                    
                # Bersihkan spasi
                nama = str(raw_nama).strip()
                alamat = str(raw_alamat).strip()

                # Cek duplikat data
                key = (nama.lower(), alamat.lower())
                if key in existing_records:
                    raise ValueError(f"Data dengan nama '{nama}' dan alamat '{alamat}' sudah terdaftar di database.")
                if key in seen_in_file:
                    raise ValueError(f"Data dengan nama '{nama}' dan alamat '{alamat}' terdeteksi ganda di dalam file.")
                
                seen_in_file.add(key)
                
                # Insert data
                sql = """INSERT INTO penduduk 
                         (nama, alamat, pendapatan, jumlah_tanggungan, luas_lahan, kepadatan_penduduk) 
                         VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (nama, alamat, pendapatan, tanggungan, lahan, kepadatan))
                imported_count += 1
                
            except Exception as row_err:
                errors.append(f"Baris {row_num}: {str(row_err)}")
                
        if errors:
            # Batalkan transaksi (rollback) jika ada baris data yang error
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Gagal mengimpor karena terdapat kesalahan data.',
                'errors': errors
            }), 400
            
        # Simpan permanen ke database jika semua baris sukses
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Berhasil mengimpor {imported_count} data penduduk secara massal.',
            'imported_count': imported_count
        }), 201
        
    except Exception as err:
        return jsonify({'status': 'error', 'message': f'Terjadi kesalahan saat memproses berkas: {str(err)}'}), 500

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

