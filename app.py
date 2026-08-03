import streamlit as st
import sqlite3
import hashlib
import datetime
import io
from docx import Document
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
    p_info.add_run("Nama Sekolah: ").bold = True
    p_info.add_run(f"{sekolah}\n")
    p_info.add_run("Kelas: ").bold = True
    p_info.add_run(f"{kelas}\n")
    p_info.add_run("Guru Wali: ").bold = True
    p_info.add_run(f"{nama_guru}\n")
    p_info.add_run("Nama Siswa: ").bold = True
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
            c.execute('''
                SELECT * FROM users WHERE username = ?
            ''', (username,))
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
                    c.execute('''
                        INSERT INTO users(username, password, nama_guru, nama_sekolah, kelas) 
                        VALUES (?,?,?,?,?)
                    ''', (new_user, make_hashes(new_password), nama_guru, nama_sekolah, kelas))
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
                c.execute('''
                    INSERT INTO students(user_id, nama_siswa, nisn) 
                    VALUES (?,?,?)
                ''', (st.session_state['user_id'], nama_siswa, nisn))
                conn.commit()
                conn.close()
                st.success(f"Siswa {nama_siswa} berhasil ditambahkan!")
                st.rerun()

        st.divider()
        st.subheader("Daftar Siswa Wali Anda")
        conn = sqlite3.connect('laporan_siswa.db')
        c = conn.cursor()
        c.execute('''
            SELECT id, nama_siswa, nisn 
            FROM students 
            WHERE user_id = ?
        ''', (st.session_state['user_id'],))
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
        c.execute('''
            SELECT id, nama_siswa 
            FROM students 
            WHERE user_id = ?
        ''', (st.session_state['user_id'],))
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
                catatan_kebiasaan = st.text_area("Catatan Kebiasaan Hari Ini:", placeholder="Contoh: Menunjukkan kedisiplinan beribadah dan membawa bekal sehat...")

            with st.expander("8 Dimensi Lulusan (Panduan & Catatan)", expanded=True):
                st.caption("Dimensi Lulusan/Profil Pelajar: Keimanan, Kewargaan, Penalaran Kritis, Kreativitas, Mandiri, Gotong Royong, Kebinekaan, Kesehatan.")
                catatan_dimensi = st.text_area("Catatan Dimensi Hari Ini:", placeholder="Contoh: Menunjukkan sikap gotong royong saat piket kelas...")

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
        c.execute('''
            SELECT id, nama_siswa, nisn 
            FROM students 
            WHERE user_id = ?
        ''', (st.session_state['user_id'],))
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
            c.execute('''
                SELECT tanggal, catatan_kebiasaan, catatan_dimensi, catatan_umum 
                FROM daily_logs 
                WHERE student_id = ? 
                ORDER BY tanggal ASC
            ''', (selected_s_id,))
            logs = c.fetchall()
            conn.close()

            if not logs:
                st.info("Siswa ini belum memiliki catatan harian.")
            else:
                st.write(f"Total catatan harian ditemukan: **{len(logs)}** catatan.")
                
                # Preview Riwayat Catatan Harian
                with st.expander("👁️ Lihat Riwayat Catatan Harian Siswa Ini"):
                    for log in logs:
                        st.markdown(f"**Tanggal:** {log[0]}")
                        st.markdown(f"- **7 Kebiasaan:** {log[1]}")
                        st.markdown(f"- **8 Dimensi:** {log[2]}")
                        st.markdown(f"- **Umum:** {log[3]}")
                        st.divider()

                st.subheader("1. Buat Evaluasi AI")
                if st.button("🤖 Generasi Rangkuman Evaluasi dengan AI"):
                    if not gemini_api_key:
                        st.error("Silakan masukkan Google Gemini API Key pada menu sidebar terlebih dahulu!")
                    else:
                        with st.spinner("Gemini AI sedang menyusun narasi evaluasi perkembangan siswa..."):
                            try:
                                genai.configure(api_key=gemini_api_key)
                                model = genai.GenerativeModel('gemini-1.5-flash')

                                prompt = f"""
                                Anda adalah seorang Guru Wali Kelas yang bijak dan profesional. 
                                Buatkan narasi evaluasi perkembangan siswa bernama '{s_nama}' berdasarkan data catatan harian berikut:
                                
                                """
                                for log in logs:
                                    prompt += f"- Tanggal {log[0]}: Kebiasaan [{log[1]}], Dimensi [{log[2]}], Catatan Lain [{log[3]}]\n"

                                prompt += """
                                Tulis narasi rangkuman perkembangan yang santun, ramah, dan mendidik untuk disampaikan kepada Orang Tua Siswa. 
                                Soroti hal positif terkait 7 Kebiasaan Anak Indonesia & 8 Dimensi Lulusan, serta berikan rekomendasi/saran untuk perkembangan anak ke depannya.
                                """

                                response = model.generate_content(prompt)
                                st.session_state[f'summary_{selected_s_id}'] = response.text
                                st.success("Rangkuman AI berhasil dibuat!")
                            except Exception as e:
                                st.error(f"Gagal memproses AI: {e}")

                # Ambil atau diedit naskah rangkuman
                summary_key = f'summary_{selected_s_id}'
                current_summary = st.session_state.get(summary_key, "")

                summary_text = st.text_area(
                    "Hasil Rangkuman Evaluasi AI (Dapat diedit/disesuaikan secara manual):",
                    value=current_summary,
                    height=250
                )
                
                # Simpan perubahan manual jika ada
                st.session_state[summary_key] = summary_text

                st.divider()
                st.subheader("2. Download Dokumen Word (.docx)")

                # TOMBOL DOWNLOAD WORD
                if summary_text.strip():
                    docx_buffer = generate_docx(
                        guru_data['nama_guru'],
                        guru_data['nama_sekolah'],
                        guru_data['kelas'],
                        s_nama,
                        s_nisn,
                        summary_text,
                        logs
                    )

                    file_name_clean = f"Laporan_Perkembangan_{s_nama.replace(' ', '_')}.docx"

                    st.download_button(
                        label="📄 Download Laporan Word (.docx)",
                        data=docx_buffer,
                        file_name=file_name_clean,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.info("💡 Klik tombol **'Generasi Rangkuman Evaluasi dengan AI'** di atas atau isi kotaknya terlebih dahulu untuk mengunduh berkas Word.")
