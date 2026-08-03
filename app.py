import streamlit as st
import sqlite3
import hashlib
import datetime
import io
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai

# ==========================================
# 1. DATABASE SETUP (Multi-User Data Isolation)
# ==========================================
def init_db():
    conn = sqlite3.connect('laporan_siswa.db')
    c = conn.cursor()
    # Tabel Guru / User
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nama_guru TEXT,
            nama_sekolah TEXT,
            kelas TEXT
        )
    ''')
    # Tabel Siswa
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nama_siswa TEXT,
            nisn TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Tabel Catatan Harian Perkembangan
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            tanggal DATE,
            catatan_kebiasaan TEXT,
            catatan_dimensi TEXT,
            catatan_umum TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# ==========================================
# 2. HELPER FUNCTIONS WORD DOCX
# ==========================================
def generate_docx(nama_guru, sekolah, kelas, nama_siswa, nisn, summary_text, logs):
    doc = Document()
    
    # Title
    title = doc.add_heading('LAPORAN PERKEMBANGAN ANAK WALI', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Identitas
    p_info = doc.add_paragraph()
    p_info.add_run(f"Nama Sekolah: ").bold = True
    p_info.add_run(f"{sekolah}\n")
    p_info.add_run(f"Kelas: ").bold = True
    p_info.add_run(f"{kelas}\n")
    p_info.add_run(f"Guru Wali: ").bold = True
    p_info.add_run(f"{nama_guru}\n")
    p_info.add_run(f"Nama Siswa: ").bold = True
    p_info.add_run(f"{nama_siswa} (NISN: {nisn})\n")
    
    doc.add_heading('1. Rangkuman Evaluasi AI (7 Kebiasaan & 8 Dimensi)', level=2)
    doc.add_paragraph(summary_text)
    
    doc.add_heading('2. Riwayat Catatan Perkembangan Harian', level=2)
    
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Tanggal'
    hdr_cells[1].text = '7 Kebiasaan Anak Indonesia'
    hdr_cells[2].text = '8 Dimensi Lulusan'
    hdr_cells[3].text = 'Catatan Umum/Lainnya'
    
    for log in logs:
        row_cells = table.add_row().cells
        row_cells[0].text = str(log[0])
        row_cells[1].text = str(log[1])
        row_cells[2].text = str(log[2])
        row_cells[3].text = str(log[3])
        
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# 3. STREAMLIT APP CONFIG & AUTHENTICATION
# ==========================================
st.set_page_config(page_title="Aplikasi Laporan Wali Kelas", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}

# Sidebar AI Key Config
st.sidebar.title("⚙️ Pengaturan AI")
gemini_api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")

# Login / Register System
if not st.session_state['logged_in']:
    st.title("🏫 Sistem Laporan Wali Kelas (7 Kebiasaan & 8 Dimensi)")
    menu = ["Login", "Daftar Akun Guru Baru"]
    choice = st.sidebar.selectbox("Menu Autentikasi", menu)

    if choice == "Login":
        st.subheader("Login Guru Wali")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            conn = sqlite3.connect('laporan_siswa.db')
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = c.fetchone()
            conn.close()
            
            if user and check_hashes(password, user[2]):
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['user_info'] = {
                    'username': user[1],
                    'nama_guru': user[3],
                    'nama_sekolah': user[4],
                    'kelas': user[5]
                }
                st.success(f"Selamat datang, {user[3]}!")
                st.rerun()
            else:
                st.error("Username atau password salah.")

    elif choice == "Daftar Akun Guru Baru":
        st.subheader("Buat Akun Guru Baru")
        new_user = st.text_input("Username Baru")
        new_password = st.text_input("Password Baru", type='password')
        nama_guru = st.text_input("Nama Lengkap Guru (beserta Gelar)")
        nama_sekolah = st.text_input("Nama Sekolah")
        kelas = st.text_input("Kelas (contoh: Kelas 5B)")

        if st.button("Daftar"):
            if new_user and new_password:
                try:
                    conn = sqlite3.connect('laporan_siswa.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO users(username, password, nama_guru, nama_sekolah, kelas) VALUES (?,?,?,?,?)',
                              (new_user, make_hashes(new_password), nama_guru, nama_sekolah, kelas))
                    conn.commit()
                    conn.close()
                    st.success("Akun berhasil dibuat! Silakan login.")
                except sqlite3.IntegrityError:
                    st.error("Username sudah digunakan, cari username lain.")
            else:
                st.warning("Mohon isi semua kolom wajib.")

# ==========================================
# 4. MAIN DASHBOARD (LOGGED IN USER)
# ==========================================
else:
    guru_data = st.session_state['user_info']
    st.sidebar.write(f"👤 **Guru:** {guru_data['nama_guru']}")
    st.sidebar.write(f"🏫 **Sekolah:** {guru_data['nama_sekolah']}")
    st.sidebar.write(f"📌 **Kelas:** {guru_data['kelas']}")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_id'] = None
        st.rerun()

    tabs = st.tabs(["📋 Data Siswa Wali", "✍️ Catatan Perkembangan Harian", "🤖 Generate AI & Download Word"])

    # ------------------------------------------
    # TAB 1: DATA SISWA
    # ------------------------------------------
    with tabs[0]:
        st.header("Identitas Guru Wali & Daftar Siswa")
        st.info(f"Guru: **{guru_data['nama_guru']}** | Sekolah: **{guru_data['nama_sekolah']}** | Kelas: **{guru_data['kelas']}**")
        
        st.subheader("Tambah Siswa Wali Baru")
        col1, col2 = st.columns(2)
        with col1:
            nama_siswa = st.text_input("Nama Lengkap Siswa")
        with col2:
            nisn = st.text_input("NISN Siswa")
            
        if st.button("Tambah Siswa"):
            if nama_siswa:
                conn = sqlite3.connect('laporan_siswa.db')
                c = conn.cursor()
                c.execute('INSERT INTO students(user_id, nama_siswa, nisn) VALUES (?,?,?)', 
                          (st.session_state['user_id'], nama_siswa, nisn))
                conn.commit()
                conn.close()
                st.success(f"Siswa {nama_siswa} berhasil ditambahkan!")
                st.rerun()

        st.divider()
        st.subheader("Daftar Siswa Wali Anda")
        conn = sqlite3.connect('laporan_siswa.db')
        c = conn.cursor()
        c.execute('SELECT id, nama_siswa, nisn FROM students WHERE user_id = ?', (st.session_state['user_id'],))
        students = c.fetchall()
        conn.close()
        
        if students:
            for s in students:
                st.write(f"- **{s[1]}** (NISN: {s[2]})")
        else:
            st.warning("Belum ada data siswa. Silakan tambahkan terlebih dahulu.")

    # ------------------------------------------
    # TAB 2: CATATAN PERKEMBANGAN HARIAN
    # ------------------------------------------
    with tabs[1]:
        st.header("Input Catatan Perkembangan Harian")
        
        conn = sqlite3.connect('laporan_siswa.db')
        c = conn.cursor()
        c.execute('SELECT id, nama_siswa FROM students WHERE user_id = ?', (st.session_state['user_id'],))
        students = c.fetchall()
        conn.close()

        if not students:
            st.warning("Silakan tambah siswa terlebih dahulu di tab 'Data Siswa Wali'.")
        else:
            student_dict = {f"{s[1]}": s[0] for s in students}
            selected_student_nama = st.selectbox("Pilih Siswa:", list(student_dict.keys()))
            selected_student_id = student_dict[selected_student_nama]

            tgl = st.date_input("Tanggal Catatan", datetime.date.today())

            st.markdown("### Focus Checklist / Catatan:")
            
            with st.expander("7 Kebiasaan Anak Indonesia Hebat (Panduan & Catatan)", expanded=True):
                st.caption("Bangun Pagi, Beribadah, Berolahraga, Gemar Membaca/Belajar, Makan Sehat, Bermasyarakat, Istirahat Cukup.")
                catatan_kebiasaan = st.text_area("Catatan Kebiasaan Hari Ini:", placeholder="Contoh: Menunjukkan kedisiplinan beribadah dan membawa bekal sehat, namun perlu diingatkan untuk istirahat tepat waktu.")

            with st.expander("8 Dimensi Lulusan (Panduan & Catatan)", expanded=True):
                st.caption("Dimensi Lulusan/Profil Pelajar: Keimanan, Kewargaan, Penalaran Kritis, Kreativitas, Mandiri, Gotong Royong, Kebinekaan, Kesehatan.")
                catatan_dimensi = st.text_area("Catatan Dimensi Hari Ini:", placeholder="Contoh: Menunjukkan sikap gotong royong saat piket kelas dan aktif mengajukan pertanyaan (penalaran kritis).")

            catatan_umum = st.text_area("Catatan Umum Tambahan:", placeholder="Catatan perilaku khusus/kejadian penting hari ini.")

            if st.button("Simpan Catatan Harian"):
                conn = sqlite3.connect('laporan_siswa.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO daily_logs(student_id, tanggal, catatan_kebiasaan, catatan_dimensi, catatan_umum)
                    VALUES (?,?,?,?,?)
                ''', (selected_student_id, tgl, catatan_kebiasaan, catatan_dimensi, catatan_umum))
                conn.commit()
                conn.close()
                st.success("Catatan perkembangan harian berhasil disimpan!")

    # ------------------------------------------
    # TAB 3: GENERATE AI & DOWNLOAD WORD
    # ------------------------------------------
    with tabs[2]:
        st.header("Rangkuman Laporan dengan AI & Download Word")

        conn = sqlite3.connect('laporan_siswa.db')
        c = conn.cursor()
        c.execute('SELECT id, nama_siswa, nisn FROM students WHERE user_id = ?', (st.session_state['user_id'],))
        students = c.fetchall()
        conn.close()

        if not students:
            st.warning("Belum ada data siswa.")
        else:
            student_dict_rep = {f"{s[1]} (NISN: {s[2]})": (s[0], s[1], s[2]) for s in students}
            selected_rep = st.selectbox("Pilih Siswa untuk Generasi Laporan:", list(student_dict_rep.keys()))
            selected_s_id, s_nama, s_nisn = student_dict_rep[selected_rep]

            # Ambil semua log siswa ini
            conn = sqlite3.connect('laporan_siswa.db')
            c = conn.cursor()
            c.execute('SELECT tanggal, catatan_kebiasaa
