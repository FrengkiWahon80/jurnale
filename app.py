import streamlit as st
import sqlite3
from datetime import datetime
import io
import docx

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Jurnal Anak Indonesia Hebat", page_icon="🇮🇩", layout="wide")

# --- 2. DATABASE INITIALIZATION (SQLite) ---
def get_connection():
    return sqlite3.connect('jurnal_sekolah.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_siswa TEXT,
            nisn TEXT UNIQUE,
            nama_kelas TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            tanggal TEXT,
            catatan_harian TEXT
        )
    ''')
    
    # Isi Data Default User dan Siswa jika database masih kosong
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, nama_lengkap, nip, role, nama_kelas) VALUES (?, ?, ?, ?, ?, ?)",
                  ('guru1', '12345', 'Budi Santoso, S.Pd.', '198501012010011001', 'guru_wali', 'Kelas 5A'))
        c.execute("INSERT INTO users (username, password, nama_lengkap, nip, role, nama_kelas) VALUES (?, ?, ?, ?, ?, ?)",
                  ('guru2', '12345', 'Siti Rahma, S.Pd.', '198802022011012002', 'guru_wali', 'Kelas 5B'))
        c.execute("INSERT INTO users (username, password, nama_lengkap, nip, role, nama_kelas) VALUES (?, ?, ?, ?, ?, ?)",
                  ('kepsek', '12345', 'Drs. Ahmad Dahlan, M.Pd.', '197003031995031001', 'kepsek', '-'))
        
        c.execute("INSERT INTO students (nama_siswa, nisn, nama_kelas) VALUES (?, ?, ?)", ('Ahmad Fauzi', '0012345678', 'Kelas 5A'))
        c.execute("INSERT INTO students (nama_siswa, nisn, nama_kelas) VALUES (?, ?, ?)", ('Siti Aminah', '0012345679', 'Kelas 5A'))
        c.execute("INSERT INTO students (nama_siswa, nisn, nama_kelas) VALUES (?, ?, ?)", ('Budi Pratama', '0012345680', 'Kelas 5B'))
        conn.commit()
    conn.close()

init_db()

# --- 3. SESSION STATE FOR LOGIN ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- 4. TAMPILAN LOGIN ---
if st.session_state['user'] is None:
    st.title("🇮🇩 Login Jurnal Anak Indonesia Hebat")
    col1, col2 = st.columns([1, 2])
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

# --- 5. TAMPILAN DASHBOARD (SETELAH LOGIN) ---
else:
    user = st.session_state['user']
    st.sidebar.title(f"Selamat Datang,\n{user['nama_lengkap']}")
    st.sidebar.write(f"**Role:** {user['role'].upper()}")
    if user['role'] == 'guru_wali':
        st.sidebar.write(f"**Kelas:** {user['nama_kelas']}")
    
    if st.sidebar.button("Logout"):
        st.session_state['user'] = None
        st.rerun()

    st.title("🇮🇩 Dashboard Jurnal & Catatan Wali Kelas")
    
    conn = get_connection()
    c = conn.cursor()

    # FILTER DATA: Guru Wali hanya melihat siswa di kelasnya
    if user['role'] == 'guru_wali':
        c.execute("SELECT * FROM students WHERE nama_kelas = ?", (user['nama_kelas'],))
    else:
        c.execute("SELECT * FROM students")
    students = c.fetchall()

    tab1, tab2 = st.tabs(["📝 Input Catatan Harian", "📄 Download Laporan Word (.docx)"])

    # TAB 1: INPUT CATATAN HARIAN WALI KELAS
    with tab1:
        st.subheader("Input Catatan Harian / Anecdotal Record")
        if students:
            student_dict = {f"{s[1]} (NISN: {s[2]})": s[0] for s in students}
            selected_student_label = st.selectbox("Pilih Siswa", list(student_dict.keys()))
            selected_student_id = student_dict[selected_student_label]

            tanggal = st.date_input("Tanggal", datetime.now())
            catatan = st.text_area("Catatan Perkembangan Harian Wali Kelas", placeholder="Tuliskan perkembangan kebiasaan / kejadian penting hari ini...")

            if st.button("Simpan Catatan Harian", type="primary"):
                c.execute("INSERT INTO journal_entries (student_id, tanggal, catatan_harian) VALUES (?, ?, ?)",
                          (selected_student_id, tanggal.strftime('%Y-%m-%d'), catatan))
                conn.commit()
                st.success("Catatan harian berhasil disimpan!")

            st.divider()
            st.subheader("Riwayat Catatan Harian Siswa Ini")
            c.execute("SELECT tanggal, catatan_harian FROM journal_entries WHERE student_id = ? ORDER BY tanggal DESC", (selected_student_id,))
            entries = c.fetchall()
            if entries:
                for e in entries:
                    st.write(f"📅 **{e[0]}**: {e[1]}")
            else:
                st.write("Belum ada riwayat catatan harian.")
        else:
            st.warning("Tidak ada data siswa untuk kelas ini.")

    # TAB 2: GENERATE LAPORAN MS WORD (.DOCX)
    with tab2:
        st.subheader("Export Laporan Word (.docx)")
        if students:
            selected_student_export = st.selectbox("Pilih Siswa untuk Download Laporan", list(student_dict.keys()), key="export_select")
            export_student_id = student_dict[selected_student_export]

            c.execute("SELECT * FROM students WHERE id = ?", (export_student_id,))
            s_data = c.fetchone()

            c.execute("SELECT * FROM users WHERE role = 'kepsek'")
            kepsek_data = c.fetchone()

            c.execute("SELECT tanggal, catatan_harian FROM journal_entries WHERE student_id = ? ORDER BY tanggal ASC", (export_student_id,))
            notes = c.fetchall()

            # MEMBUAT DOKUMEN WORD (.DOCX) SECARA DINAMIS
            doc = docx.Document()
            doc.add_heading('LAPORAN JURNAL KEBIASAAN & CATATAN HARIAN', 0)
            doc.add_paragraph(f"Nama Siswa : {s_data[1]}")
            doc.add_paragraph(f"NISN       : {s_data[2]}")
            doc.add_paragraph(f"Kelas      : {s_data[3]}")
            doc.add_paragraph(f"Periode    : {datetime.now().strftime('%B %Y')}")

            doc.add_heading('REKAP CATATAN HARIAN WALI KELAS', level=1)
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Tanggal'
            hdr_cells[1].text = 'Catatan Harian Wali Kelas'

            if notes:
                for n in notes:
                    row_cells = table.add_row().cells
                    row_cells[0].text = n[0]
                    row_cells[1].text = n[1]
            else:
                row_cells = table.add_row().cells
                row_cells[0].text = "-"
                row_cells[1].text = "Belum ada catatan harian."

            doc.add_paragraph("\n\n")
            doc.add_paragraph(f"Guru Wali Kelas: {user['nama_lengkap']} (NIP. {user['nip']})")
            if kepsek_data:
                doc.add_paragraph(f"Kepala Sekolah : {kepsek_data[3]} (NIP. {kepsek_data[4]})")

            # Simpan ke Buffer RAM untuk diunduh
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)

            st.download_button(
                label="📥 Download Laporan Word (.docx)",
                data=bio,
                file_name=f"Laporan_{s_data[1].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    conn.close()
