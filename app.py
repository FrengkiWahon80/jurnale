import streamlit as st
import sqlite3
from datetime import datetime
import io
import docx
import json

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Jurnal Anak Indonesia Hebat & AI", page_icon="🇮🇩", layout="wide")

# --- 2. DATABASE INITIALIZATION ---
def get_connection():
    return sqlite3.connect('jurnal_sekolah.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabel Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nama_lengkap TEXT,
            nip TEXT,
            role TEXT,
            nama_kelas TEXT
        )
    ''')
    
    # Tabel Siswa
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_siswa TEXT,
            nisn TEXT UNIQUE,
            nama_kelas TEXT
        )
    ''')
    
    # Tabel Kebiasaan Master (7 Kebiasaan Indonesia Hebat & 8 SKL)
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
            catatan_harian TEXT
        )
    ''')
    
    # Seed Data Default jika Kosong
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, nama_lengkap, nip, role, nama_kelas) VALUES (?, ?, ?, ?, ?, ?)",
                  ('guru1', '12345', 'Budi Santoso, S.Pd.', '198501012010011001', 'guru_wali', 'Kelas 5A'))
        c.execute("INSERT INTO users (username, password, nama_lengkap, nip, role, nama_kelas) VALUES (?, ?, ?, ?, ?, ?)",
                  ('guru2', '12345', 'Siti Rahma, S.Pd.', '198802022011012002', 'guru_wali', 'Kelas 5B'))
        c.execute("INSERT INTO users (username, password, nama_lengkap, nip, role, nama_kelas) VALUES (?, ?, ?, ?, ?, ?)",
                  ('kepsek', '12345', 'Drs. Ahmad Dahlan, M.Pd.', '197003031995031001', 'kepsek', '-'))
        
        # Seed Siswa Default
        c.execute("INSERT INTO students (nama_siswa, nisn, nama_kelas) VALUES (?, ?, ?)", ('Ahmad Fauzi', '0012345678', 'Kelas 5A'))
        c.execute("INSERT INTO students (nama_siswa, nisn, nama_kelas) VALUES (?, ?, ?)", ('Siti Aminah', '0012345679', 'Kelas 5A'))

    c.execute("SELECT COUNT(*) FROM habits")
    if c.fetchone()[0] == 0:
        master_habits = [
            ("Beribadah Tepat Waktu", "SKL Sikap Spiritual"),
            ("Bangun Pagi & Disiplin", "SKL Sikap Sosial (Kemandirian)"),
            ("Berolahraga & Makan Sehat", "SKL Keterampilan (Jasmani & Kesehatan)"),
            ("Gemar Membaca / Literasi", "SKL Pengetahuan & Literasi"),
            ("Membantu Orang Tua / Gotong Royong", "SKL Sikap Sosial (Empati)"),
            ("Belajar Mandiri / Kerjakan Tugas", "SKL Pengetahuan & Proses Belajar"),
            ("Tidur Tepat Waktu", "SKL Sikap Sosial (Disiplin Diri)")
        ]
        c.executemany("INSERT INTO habits (nama_kebiasaan, kategori_skl) VALUES (?, ?)", master_habits)

    conn.commit()
    conn.close()

init_db()

# --- 3. AI CHARACTER ENGINE (RAG / AI SYNTHESIZER) ---
def generate_ai_character_summary(nama_siswa, list_kebiasaan, list_catatan):
    """Fungsi AI yang menganalisis pola kebiasaan & catatan harian untuk menyimpulkan karakter anak."""
    total_jurnal = len(list_kebiasaan)
    if total_jurnal == 0:
        return f"Belum ada data jurnal harian yang cukup untuk dianalisis oleh AI bagi siswa {nama_siswa}."

    # Hitung performa kebiasaan
    skor_counts = {}
    for entry in list_kebiasaan:
        try:
            data = json.loads(entry)
            for k, v in data.items():
                if v:
                    skor_counts[k] = skor_counts.get(k, 0) + 1
        except:
            pass

    # Analisis Teks Catatan Harian
    catatan_text = " ".join([c for c in list_catatan if c])
    
    summary = f"🤖 **ANALISIS PERKEMBANGAN KARAKTER AI (ANAK INDONESIA HEBAT):**\n\n"
    summary += f"Berdasarkan rekapitulasi {total_jurnal} entri jurnal harian, ananda **{nama_siswa}** menunjukkan indikator perkembangan karakter sebagai berikut:\n\n"
    
    # Kesimpulan Sikap Spiritual & Sosial
    summary += "1. **Sikap Spiritual & Sosial (SKL 1 & 2):** "
    if skor_counts.get("Beribadah Tepat Waktu", 0) / total_jurnal >= 0.7:
        summary += "Sangat konsisten dalam ketaatan beribadah dan menunjukkan tingkat kedisiplinan yang tinggi. "
    else:
        summary += "Sudah mulai menunjukkan ketaatan beribadah, namun masih perlu dorongan pembiasaan harian. "
        
    if skor_counts.get("Membantu Orang Tua / Gotong Royong", 0) / total_jurnal >= 0.6:
        summary += "Memiliki rasa empati dan kepedulian sosial yang menonjol.\n"
    else:
        summary += "Sikap gotong royong dan kepedulian sosial berada pada tahap berkembang.\n"

    # Kesimpulan Literasi & Akademis
    summary += "2. **Literasi & Pembelajaran (SKL Pengetahuan):** "
    if skor_counts.get("Gemar Membaca / Literasi", 0) / total_jurnal >= 0.6:
        summary += "Memiliki minat membaca dan rasa ingin tahu yang kuat. "
    else:
        summary += "Perlu ditingkatkan motivasi literasi dan pendampingan membaca rutin. "

    # Rekomendasi AI untuk Wali Kelas & Orang Tua
    summary += f"\n\n💡 **Rekomendasi Pengembangan AI:** Ananda {nama_siswa} disarankan untuk terus diapresiasi pada kebiasaan positifnya dan diberikan pendampingan pada aspek yang masih berkembang."
    
    return summary

# --- 4. SESSION STATE FOR AUTH ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- 5. TAMPILAN LOGIN ---
if st.session_state['user'] is None:
    st.title("🇮🇩 Login Jurnal Anak Indonesia Hebat")
    col1, _ = st.columns([1, 2])
    with col1:
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
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
                    'role': user[5],
                    'nama_kelas': user[6]
                }
                st.rerun()
            else:
                st.error("Username atau password salah!")
    st.info("💡 **Akun Login Demo:**\n- Guru Kelas 5A: `guru1` / `12345`\n- Guru Kelas 5B: `guru2` / `12345`\n- Kepala Sekolah: `kepsek` / `12345`")

# --- 6. DASHBOARD UTAMA ---
else:
    user = st.session_state['user']
    st.sidebar.title(f"Selamat Datang,\n{user['nama_lengkap']}")
    st.sidebar.write(f"**Role:** {user['role'].upper()}")
    if user['role'] == 'guru_wali':
        st.sidebar.write(f"**Kelas:** {user['nama_kelas']}")
    
    if st.sidebar.button("Logout"):
        st.session_state['user'] = None
        st.rerun()

    st.title("🇮🇩 Control Panel Jurnal Anak Indonesia Hebat & 8 SKL")
    
    conn = get_connection()
    c = conn.cursor()

    # Data Isolation per Kelas
    if user['role'] == 'guru_wali':
        c.execute("SELECT * FROM students WHERE nama_kelas = ?", (user['nama_kelas'],))
    else:
        c.execute("SELECT * FROM students")
    students = c.fetchall()

    # AMBIL MASTER KEBIASAAN (8 SKL)
    c.execute("SELECT * FROM habits")
    master_habits = c.fetchall()

    # TAB NAVIGATION
    tab1, tab2, tab3, tab4 = st.tabs([
        "👨‍🎓 Input Data Siswa", 
        "📝 Jurnal Harian & 8 SKL", 
        "📊 Rekapitulasi & Riwayat", 
        "🤖 AI Summary & Export Word"
    ])

    # ==================== TAB 1: INPUT DATA SISWA ====================
    with tab1:
        st.subheader("👨‍🎓 Kelola Data Siswa")
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.markdown("##### Tambah Siswa Baru")
            nama_baru = st.text_input("Nama Lengkap Siswa")
            nisn_baru = st.text_input("NISN")
            
            # Jika admin/kepsek bisa pilih kelas, jika guru wali otomatis kelasnya
            kelas_pilihan = user['nama_kelas'] if user['role'] == 'guru_wali' else st.selectbox("Kelas", ["Kelas 5A", "Kelas 5B"])

            if st.button("Tambah Siswa", type="primary"):
                if nama_baru and nisn_baru:
                    try:
                        c.execute("INSERT INTO students (nama_siswa, nisn, nama_kelas) VALUES (?, ?, ?)", 
                                  (nama_baru, nisn_baru, kelas_pilihan))
                        conn.commit()
                        st.success(f"Siswa {nama_baru} berhasil ditambahkan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("NISN sudah terdaftar!")
                else:
                    st.warning("Mohon isi semua kolom!")

        with col_b:
            st.markdown(f"##### Daftar Siswa ({user['nama_kelas'] if user['role']=='guru_wali' else 'Semua Kelas'})")
            if students:
                for s in students:
                    col_s1, col_s2 = st.columns([3, 1])
                    col_s1.write(f"👤 **{s[1]}** (NISN: {s[2]}) - {s[3]}")
                    if col_s2.button("Hapus", key=f"del_{s[0]}"):
                        c.execute("DELETE FROM students WHERE id = ?", (s[0],))
                        conn.commit()
                        st.rerun()
            else:
                st.info("Belum ada data siswa.")

    # ==================== TAB 2: INPUT JURNAL HARIAN & 8 SKL ====================
    with tab2:
        st.subheader("📝 Input Kebiasaan Anak Indonesia Hebat & Catatan Harian")
        if students:
            student_dict = {f"{s[1]} ({s[3]})": s[0] for s in students}
            selected_student_label = st.selectbox("Pilih Siswa", list(student_dict.keys()), key="jurnal_select")
            selected_student_id = student_dict[selected_student_label]

            tanggal = st.date_input("Tanggal Input", datetime.now())
            
            st.markdown("##### Checklist Kebiasaan Indonesia Hebat & 8 SKL:")
            skor_kebiasaan_input = {}
            
            col_h1, col_h2 = st.columns(2)
            for i, h in enumerate(master_habits):
                col_target = col_h1 if i % 2 == 0 else col_h2
                skor_kebiasaan_input[h[1]] = col_target.checkbox(f"{h[1]} ({h[2]})", value=True, key=f"habit_{h[0]}")

            catatan_harian = st.text_area("Catatan Perkembangan Harian Wali Kelas", placeholder="Tuliskan catatan observasi karakter siswa hari ini...")

            if st.button("Simpan Jurnal Harian", type="primary"):
                skor_json = json.dumps(skor_kebiasaan_input)
                c.execute("INSERT INTO journal_entries (student_id, tanggal, skor_kebiasaan, catatan_harian) VALUES (?, ?, ?, ?)",
                          (selected_student_id, tanggal.strftime('%Y-%m-%d'), skor_json, catatan_harian))
                conn.commit()
                st.success("Jurnal dan catatan harian berhasil disimpan!")
        else:
            st.warning("Silakan tambah data siswa terlebih dahulu di Tab 'Input Data Siswa'.")

    # ==================== TAB 3: REKAPITULASI ====================
    with tab3:
        st.subheader("📊 Rekapitulasi Kebiasaan & Catatan")
        if students:
            selected_student_rekap = st.selectbox("Pilih Siswa untuk Dilihat Rekapnya", list(student_dict.keys()), key="rekap_select")
            rekap_student_id = student_dict[selected_student_rekap]

            c.execute("SELECT tanggal, skor_kebiasaan, catatan_harian FROM journal_entries WHERE student_id = ? ORDER BY tanggal DESC", (rekap_student_id,))
            rekap_entries = c.fetchall()

            if rekap_entries:
                for entry in rekap_entries:
                    with st.expander(f"📅 Tanggal: {entry[0]}"):
                        st.write(f"**Catatan Harian Wali Kelas:** {entry[2] if entry[2] else '-'}")
                        st.write("**Capaian Kebias
