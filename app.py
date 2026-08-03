import streamlit as st
import sqlite3
from datetime import datetime
import io
import docx
import json

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Jurnal SMPN Tujuh Maret Hadakewa", page_icon="🏫", layout="wide")

DEFAULT_SEKOLAH = "SMPN Tujuh Maret Hadakewa"

# --- 2. DATABASE INITIALIZATION ---
def get_connection():
    return sqlite3.connect('jurnal_sekolah.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabel Users (Dengan Identitas Guru & Sekolah)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nama_lengkap TEXT,
            nip TEXT,
            nama_sekolah TEXT DEFAULT 'SMPN Tujuh Maret Hadakewa',
            nama_kelas TEXT,
            role TEXT DEFAULT 'guru_wali'
        )
    ''')
    
    # Tabel Kepala Sekolah (Satu Sekolah)
    c.execute('''
        CREATE TABLE IF NOT EXISTS kepsek (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_kepsek TEXT,
            nip_kepsek TEXT,
            nama_sekolah TEXT DEFAULT 'SMPN Tujuh Maret Hadakewa'
        )
    ''')
    
    # Tabel Siswa (Terikat pada ID Guru agar Data Tidak Tercampur)
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guru_id INTEGER,
            nama_siswa TEXT,
            nisn TEXT,
            nama_kelas TEXT,
            FOREIGN KEY(guru_id) REFERENCES users(id)
        )
    ''')
    
    # Tabel Kebiasaan Master (7 Kebiasaan Anak Indonesia Hebat SMP & 8 SKL)
    c.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_kebiasaan TEXT,
            kategori_skl TEXT
        )
    ''')
    
    # Tabel Jurnal Harian
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            tanggal TEXT,
            skor_kebiasaan TEXT,
            catatan_harian TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    
    # Seed Data Default Kepsek jika Kosong
    c.execute("SELECT COUNT(*) FROM kepsek")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO kepsek (nama_kepsek, nip_kepsek, nama_sekolah) VALUES (?, ?, ?)",
                  ('Kepala Sekolah, M.Pd.', '197501012000121001', DEFAULT_SEKOLAH))

    # Seed Master Kebiasaan SMP
    c.execute("SELECT COUNT(*) FROM habits")
    if c.fetchone()[0] == 0:
        master_habits = [
            ("Beribadah Tepat Waktu & Berakhlak Mulia", "SKL Sikap Spiritual"),
            ("Bangun Pagi & Disiplin Diri", "SKL Sikap Sosial (Kemandirian)"),
            ("Berolahraga & Menjaga Kesehatan", "SKL Keterampilan (Jasmani & Kesehatan)"),
            ("Gemar Membaca / Literasi Buku", "SKL Pengetahuan & Literasi"),
            ("Gotong Royong & Kepedulian Lingkungan", "SKL Sikap Sosial (Empati)"),
            ("Belajar Mandiri & Pemanfaatan Teknologi", "SKL Pengetahuan & Proses Belajar"),
            ("Tidur Tepat Waktu & Istirahat Cukup", "SKL Sikap Sosial (Disiplin Diri)")
        ]
        c.executemany("INSERT INTO habits (nama_kebiasaan, kategori_skl) VALUES (?, ?)", master_habits)

    conn.commit()
    conn.close()

init_db()

# --- 3. AI CHARACTER ENGINE ---
def generate_ai_character_summary(nama_siswa, list_kebiasaan, list_catatan):
    total_jurnal = len(list_kebiasaan)
    if total_jurnal == 0:
        return f"Belum ada data jurnal harian yang cukup untuk dianalisis bagi siswa {nama_siswa}."

    skor_counts = {}
    for entry in list_kebiasaan:
        try:
            data = json.loads(entry)
            for k, v in data.items():
                if v:
                    skor_counts[k] = skor_counts.get(k, 0) + 1
        except Exception:
            pass

    summary = f"🤖 ANALISIS PERKEMBANGAN KARAKTER AI (SMPN TUJUH MARET HADAKEWA):\n\n"
    summary += f"Berdasarkan rekapitulasi {total_jurnal} entri jurnal harian, ananda {nama_siswa} menunjukkan indikator perkembangan karakter sebagai berikut:\n\n"
    
    summary += "1. Sikap Spiritual & Sosial (SKL 1 & 2): "
    if skor_counts.get("Beribadah Tepat Waktu & Berakhlak Mulia", 0) / max(total_jurnal, 1) >= 0.7:
        summary += "Sangat baik dalam ketaatan beribadah dan menunjukkan tingkat kedisiplinan yang tinggi. "
    else:
        summary += "Sudah mulai menunjukkan ketaatan beribadah, namun masih perlu dorongan pembiasaan harian. "
        
    if skor_counts.get("Gotong Royong & Kepedulian Lingkungan", 0) / max(total_jurnal, 1) >= 0.6:
        summary += "Memiliki rasa empati dan kepedulian sosial yang sangat baik di lingkungan sekolah.\n"
    else:
        summary += "Sikap gotong royong dan kepedulian sosial berada pada tahap berkembang.\n"

    summary += "2. Literasi & Pembelajaran SMP (SKL Pengetahuan): "
    if skor_counts.get("Gemar Membaca / Literasi Buku", 0) / max(total_jurnal, 1) >= 0.6:
        summary += "Memiliki minat membaca dan kemandirian belajar yang kuat. "
    else:
        summary += "Perlu ditingkatkan motivasi literasi dan pemanfaatan waktu belajar mandiri. "

    summary += f"\n\n💡 Rekomendasi AI: Ananda {nama_siswa} disarankan untuk terus diapresiasi pada kebiasaan positifnya serta diberikan pendampingan pada aspek pembiasaan yang masih berkembang."
    
    return summary

# --- 4. SESSION STATE FOR AUTH ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- 5. TAMPILAN LOGIN & REGISTRASI ---
if st.session_state['user'] is None:
    st.title("🏫 Jurnal Guru - SMPN Tujuh Maret Hadakewa")
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login Guru", "📝 Daftar Akun Guru Baru"])
    
    with auth_tab1:
        col1, _ = st.columns([1, 2])
        with col1:
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            if st.button("Masuk Aplikasi", type="primary"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username_input, password_input))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['user'] = {
                        'id': user[0],
                        'username': user[1],
                        'nama_lengkap': user[3],
                        'nip': user[4],
                        'nama_sekolah': user[5],
                        'nama_kelas': user[6],
                        'role': user[7]
                    }
                    st.rerun()
                else:
                    st.error("Username atau password salah!")

    with auth_tab2:
        st.markdown("##### Registrasi Akun Guru Wali Kelas Baru")
        reg_nama = st.text_input("Nama Lengkap Guru (dengan Gelar)")
        reg_nip = st.text_input("NIP Guru")
        reg_kelas = st.selectbox("Wali Kelas", ["Kelas 7A", "Kelas 7B", "Kelas 7C", "Kelas 8A", "Kelas 8B", "Kelas 9A", "Kelas 9B"])
        reg_username = st.text_input("Username Baru")
        reg_password = st.text_input("Password Baru", type="password")
        
        if st.button("Daftar Akun", type="secondary"):
            if reg_nama and reg_username and reg_password:
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, password, nama_lengkap, nip, nama_sekolah, nama_kelas, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (reg_username, reg_password, reg_nama, reg_nip, DEFAULT_SEKOLAH, reg_kelas, 'guru_wali'))
                    conn.commit()
                    conn.close()
                    st.success("Akun berhasil dibuat! Silakan Login di tab sebelah.")
                except sqlite3.IntegrityError:
                    st.error("Username sudah digunakan. Silakan pilih username lain.")
            else:
                st.warnin
