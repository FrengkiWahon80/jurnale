import datetime
import hashlib
import io
import os
import sqlite3
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai
import streamlit as st


# ==========================================
# 1. DATABASE SETUP (Multi-User Data Isolation)
# ==========================================
def init_db():
  conn = sqlite3.connect("laporan_siswa.db")
  c = conn.cursor()
  # Tabel Guru / User
  c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nama_guru TEXT,
            nama_sekolah TEXT
        )
    """)
  # Tabel Siswa (Terisolasi berdasarkan user_id / guru)
  c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nama_siswa TEXT,
            nisn TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
  # Tabel Catatan Harian Perkembangan
  c.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            tanggal DATE,
            catatan_kebiasaan TEXT,
            catatan_dimensi TEXT,
            catatan_umum TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
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
# 2. GENERATOR RANGKUMAN (AI / FALLBACK TEMPLATE)
# ==========================================
def generate_summary(nama_siswa, logs):
  api_key = st.secrets.get(
      "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")
  )

  if api_key:
    try:
      genai.configure(api_key=api_key)
      model = genai.GenerativeModel("gemini-1.5-flash")
      prompt = f"""
            Anda adalah seorang Guru Wali Kelas yang bijak dan profesional. 
            Buatkan narasi evaluasi perkembangan siswa bernama '{nama_siswa}' berdasarkan data catatan harian berikut:
            """
      for log in logs:
        kebiasaan = (
            log[1] if (log[1] and str(log[1]).strip()) else "Tidak ada catatan"
        )
        dimensi = (
            log[2] if (log[2] and str(log[2]).strip()) else "Tidak ada catatan"
        )
        umum = (
            log[3] if (log[3] and str(log[3]).strip()) else "Tidak ada catatan"
        )

        prompt += f"- Tanggal {log[0]}: Kebiasaan [{kebiasaan}], Dimensi [{dimensi}], Catatan Lain [{umum}]\n"

      prompt += """
            Tulis narasi rangkuman perkembangan yang santun, ramah, dan mendidik untuk disampaikan kepada Orang Tua Siswa. 
            Soroti hal positif terkait 7 Kebiasaan Anak Indonesia & 8 Dimensi Lulusan, serta berikan rekomendasi/saran untuk perkembangan anak ke depannya.
            """
      response = model.generate_content(prompt)
      return response.text
    except Exception as e:
      st.warning(
          f"Sistem AI mengalami kendala ({e}). Mengalihkan ke generator narasi"
          " internal..."
      )

  # FALLBACK NARRATIVE (Jika Tidak Ada API Key / Terjadi Error)
  kebiasaan_list = [
      f"• Tanggal {l[0]}: {l[1]}"
      for l in logs
      if l[1] and str(l[1]).strip()
  ]
  dimensi_list = [
      f"• Tanggal {l[0]}: {l[2]}"
      for l in logs
      if l[2] and str(l[2]).strip()
  ]
  umum_list = [
      f"• Tanggal {l[0]}: {l[3]}"
      for l in logs
      if l[3] and str(l[3]).strip()
  ]

  narasi = f"**RANGKUMAN EVALUASI PERKEMBANGAN SISWA**\n\n"
  narasi += f"Yth. Bapak/Ibu Orang Tua/Wali dari **{nama_siswa}**,\n\n"
  narasi += (
      "Berikut adalah ringkasan perkembangan ananda selama periode pencatatan"
      " harian di sekolah:\n\n"
  )

  narasi += "📌 **1. Perkembangan 7 Kebiasaan Anak Indonesia:**\n"
  if kebiasaan_list:
    narasi += "\n".join(kebiasaan_list) + "\n\n"
  else:
    narasi += (
        "Ananda menunjukkan sikap umum yang cukup baik dalam pembiasaan"
        " harian.\n\n"
    )

  narasi += "📌 **2. Perkembangan 8 Dimensi Lulusan:**\n"
  if dimensi_list:
    narasi += "\n".join(dimensi_list) + "\n\n"
  else:
    narasi += (
        "Ananda terus berproses dalam menginternalisasi nilai-nilai karakter"
        " lulusan.\n\n"
    )

  if umum_list:
    narasi += "📌 **3. Catatan Khusus & Kejadian Penting:**\n"
    narasi += "\n".join(umum_list) + "\n\n"

  narasi += "💡 **Rekomendasi & Apresiasi Guru:**\n"
  narasi += (
      f"Secara umum, Ananda **{nama_siswa}** menunjukkan perkembangan"
      " karakter yang positif. Mohon dukungan Bapak/Ibu di rumah untuk terus"
      " memotivasi ananda dalam mempertahankan kebiasaan baik ini."
  )

  return narasi


# ==========================================
# 3. HELPER FUNCTIONS WORD DOCX
# ==========================================
def generate_docx(nama_guru, sekolah, nama_siswa, nisn, summary_text, logs):
  doc = Document()

  # Title
  title = doc.add_heading("LAPORAN PERKEMBANGAN SISWA", level=1)
  title.alignment = WD_ALIGN_PARAGRAPH.CENTER

  # Identitas
  p_info = doc.add_paragraph()
  p_info.add_run("Nama Sekolah: ").bold = True
  p_info.add_run(f"{sekolah}\n")
  p_info.add_run("Guru Wali: ").bold = True
  p_info.add_run(f"{nama_guru}\n")
  p_info.add_run("Nama Siswa: ").bold = True
  p_info.add_run(f"{nama_siswa} (NISN: {nisn})\n")

  doc.add_heading(
      "1. Rangkuman Evaluasi Perkembangan (7 Kebiasaan & 8 Dimensi)", level=2
  )
  doc.add_paragraph(summary_text)

  doc.add_heading("2. Riwayat Catatan Perkembangan Harian", level=2)

  table = doc.add_table(rows=1, cols=4)
  table.style = "Table Grid"
  hdr_cells = table.rows[0].cells
  hdr_cells[0].text = "Tanggal"
  hdr_cells[1].text = "7 Kebiasaan Anak Indonesia"
  hdr_cells[2].text = "8 Dimensi Lulusan"
  hdr_cells[3].text = "Catatan Umum/Lainnya"

  for log in logs:
    row_cells = table.add_row().cells
    row_cells[0].text = str(log[0]) if log[0] else "-"
    row_cells[1].text = str(log[1]) if (log[1] and str(log[1]).strip()) else "-"
    row_cells[2].text = str(log[2]) if (log[2] and str(log[2]).strip()) else "-"
    row_cells[3].text = str(log[3]) if (log[3] and str(log[3]).strip()) else "-"

  bio = io.BytesIO()
  doc.save(bio)
  bio.seek(0)
  return bio


# ==========================================
# 4. STREAMLIT APP CONFIG & AUTHENTICATION
# ==========================================
st.set_page_config(
    page_title="Sistem Laporan Siswa - SMPN 7 Maret Hadakewa", layout="wide"
)

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
  st.session_state["user_id"] = None
if "user_info" not in st.session_state:
  st.session_state["user_info"] = {}

# Login / Register System
if not st.session_state["logged_in"]:
  st.title("🏫 Sistem Laporan Perkembangan Siswa")
  st.caption("SMPN Tujuh Maret Hadakewa")

  menu = ["Login Guru", "Daftar Akun Guru Baru"]
  choice = st.sidebar.selectbox("Menu Autentikasi", menu)

  if choice == "Login Guru":
    st.subheader("🔑 Login Guru Wali")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
      conn = sqlite3.connect("laporan_siswa.db")
      c = conn.cursor()
      c.execute(
          """
                SELECT id, username, password, nama_guru, nama_sekolah 
                FROM users WHERE username = ?
            """,
          (username,),
      )
      user = c.fetchone()
      conn.close()

      if user and check_hashes(password, user[2]):
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = user[0]
        st.session_state["user_info"] = {
            "username": user[1],
            "nama_guru": user[3],
            "nama_sekolah": user[4],
        }
        st.success(f"Selamat datang, {user[3]}!")
        st.rerun()
      else:
        st.error("Username atau password salah.")

  elif choice == "Daftar Akun Guru Baru":
    st.subheader("📝 Buat Akun Guru Baru")
    new_user = st.text_input("Username Baru")
    new_password = st.text_input("Password Baru", type="password")
    nama_guru = st.text_input("Nama Lengkap Guru (beserta Gelar)")
    nama_sekolah = st.text_input(
        "Nama Sekolah", value="SMPN Tujuh Maret Hadakewa"
    )

    if st.button("Daftar Akun"):
      if new_user and new_password and nama_guru:
        try:
          conn = sqlite3.connect("laporan_siswa.db")
          c = conn.cursor()
          c.execute(
              """
                        INSERT INTO users(username, password, nama_guru, nama_sekolah) 
                        VALUES (?,?,?,?)
                    """,
              (new_user, make_hashes(new_password), nama_guru, nama_sekolah),
          )
          conn.commit()
          conn.close()
          st.success(
              "Akun berhasil dibuat! Silakan pilih menu 'Login Guru' pada"
              " sidebar."
          )
        except sqlite3.IntegrityError:
          st.error("Username sudah digunakan, silakan pilih username lain.")
      else:
        st.warning("Mohon lengkapi semua data pendaftaran.")

# ==========================================
# 5. MAIN DASHBOARD (LOGGED IN USER)
# ==========================================
else:
  guru_data = st.session_state["user_info"]
  st.sidebar.title("📌 Akun Guru")
  st.sidebar.write(f"👤 **Guru:** {guru_data['nama_guru']}")
  st.sidebar.write(f"🏫 **Sekolah:** {guru_data['nama_sekolah']}")

  if st.sidebar.button("Logout", type="secondary"):
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.rerun()

  tabs = st.tabs([
      "📋 Data Siswa",
      "✍️ Catatan Perkembangan Harian",
      "📄 Generate Laporan & Download Word",
  ])

  # ------------------------------------------
  # TAB 1: DATA SISWA WALI
  # ------------------------------------------
  with tabs[0]:
    st.header("Kelola Data Siswa")
    st.info(
        f"Guru: **{guru_data['nama_guru']}** | Sekolah:"
        f" **{guru_data['nama_sekolah']}**"
    )

    st.subheader("Tambah Siswa Baru")
    col1, col2 = st.columns(2)
    with col1:
      nama_siswa = st.text_input("Nama Lengkap Siswa")
    with col2:
      nisn = st.text_input("NISN Siswa")

    if st.button("Tambah Siswa", type="primary"):
      if nama_siswa:
        conn = sqlite3.connect("laporan_siswa.db")
        c = conn.cursor()
        c.execute(
            """
                    INSERT INTO students(user_id, nama_siswa, nisn) 
                    VALUES (?,?,?)
                """,
            (st.session_state["user_id"], nama_siswa, nisn),
        )
        conn.commit()
        conn.close()
        st.success(f"Siswa {nama_siswa} berhasil ditambahkan!")
        st.rerun()
      else:
        st.warning("Nama siswa wajib diisi!")

    st.divider()
    st.subheader("Daftar Siswa Kelolaan Anda")
    conn = sqlite3.connect("laporan_siswa.db")
    c = conn.cursor()
    c.execute(
        """
            SELECT id, nama_siswa, nisn 
            FROM students 
            WHERE user_id = ?
        """,
        (st.session_state["user_id"],),
    )
    students = c.fetchall()
    conn.close()

    if students:
      for s in students:
        st.write(f"- **{s[1]}** (NISN: {s[2]})")
    else:
      st.info("Belum ada data siswa. Silakan tambahkan siswa di atas.")

  # ------------------------------------------
  # TAB 2: CATATAN HARIAN
  # ------------------------------------------
  with tabs[1]:
    st.header("Input Catatan Perkembangan Harian")

    conn = sqlite3.connect("laporan_siswa.db")
    c = conn.cursor()
    c.execute(
        """
            SELECT id, nama_siswa 
            FROM students 
            WHERE user_id = ?
        """,
        (st.session_state["user_id"],),
    )
    students = c.fetchall()
    conn.close()

    if not students:
      st.warning(
          "Silakan tambahkan siswa terlebih dahulu pada tab 'Data Siswa'."
      )
    else:
      student_dict = {f"{s[1]}": s[0] for s in students}
      selected_student_nama = st.selectbox(
          "Pilih Siswa:", list(student_dict.keys())
      )
      selected_student_id = student_dict[selected_student_nama]

      tgl = st.date_input("Tanggal Catatan", datetime.date.today())

      st.markdown("### Focus Checklist / Catatan:")

      with st.expander("7 Kebiasaan Anak Indonesia Hebat", expanded=True):
        st.caption(
            "Bangun Pagi, Beribadah, Berolahraga, Gemar Membaca/Belajar, Makan"
            " Sehat, Bermasyarakat, Istirahat Cukup."
        )
        catatan_kebiasaan = st.text_area(
            "Catatan Kebiasaan Hari Ini:",
            placeholder=(
                "Contoh: Kedisiplinan beribadah dan membawa bekal sehat..."
            ),
        )

      with st.expander("8 Dimensi Lulusan", expanded=True):
        st.caption(
            "Keimanan, Kewargaan, Penalaran Kritis, Kreativitas, Mandiri, Gotong"
            " Royong, Kebinekaan, Kesehatan."
        )
        catatan_dimensi = st.text_area(
            "Catatan Dimensi Hari Ini:",
            placeholder=(
                "Contoh: Menunjukkan sikap gotong royong saat piket..."
            ),
        )

      catatan_umum = st.text_area(
          "Catatan Umum Tambahan:",
          placeholder="Catatan perilaku khusus/kejadian penting hari ini.",
      )

      if st.button("Simpan Catatan Harian", type="primary"):
        conn = sqlite3.connect("laporan_siswa.db")
        c = conn.cursor()
        c.execute(
            """
                    INSERT INTO daily_logs(student_id, tanggal, catatan_kebiasaan, catatan_dimensi, catatan_umum)
                    VALUES (?,?,?,?,?)
                """,
            (
                selected_student_id,
                tgl,
                catatan_kebiasaan,
                catatan_dimensi,
                catatan_umum,
            ),
        )
        conn.commit()
        conn.close()
        st.success("Catatan perkembangan harian berhasil disimpan!")

  # ------------------------------------------
  # TAB 3: GENERATE & DOWNLOAD WORD
  # ------------------------------------------
  with tabs[2]:
    st.header("Rangkuman Laporan & Download Word")

    conn = sqlite3.connect("laporan_siswa.db")
    c = conn.cursor()
    c.execute(
        """
            SELECT id, nama_siswa, nisn 
            FROM students 
            WHERE user_id = ?
        """,
        (st.session_state["user_id"],),
    )
    students = c.fetchall()
    conn.close()

    if not students:
      st.warning("Belum ada data siswa.")
    else:
      student_dict_rep = {
          f"{s[1]} (NISN: {s[2]})": (s[0], s[1], s[2]) for s in students
      }
      selected_rep = st.selectbox(
          "Pilih Siswa untuk Generasi Laporan:", list(student_dict_rep.keys())
      )
      selected_s_id, s_nama, s_nisn = student_dict_rep[selected_rep]

      # Ambil semua log milik siswa terpilih
      conn = sqlite3.connect("laporan_siswa.db")
      c = conn.cursor()
      c.execute(
          """
                SELECT tanggal, catatan_kebiasaan, catatan_dimensi, catatan_umum 
                FROM daily_logs 
                WHERE student_id = ? 
                ORDER BY tanggal ASC
            """,
          (selected_s_id,),
      )
      logs = c.fetchall()
      conn.close()

      if not logs:
        st.info("Siswa ini belum memiliki catatan harian.")
      else:
        st.write(f"Total catatan harian ditemukan: **{len(logs)}** catatan.")

        with st.expander("👁️ Lihat Riwayat Catatan Harian Siswa Ini"):
          for log in logs:
            st.markdown(f"**Tanggal:** {log[0]}")
            st.markdown(f"- **7 Kebiasaan:** {log[1] if log[1] else '-'}")
            st.markdown(f"- **8 Dimensi:** {log[2] if log[2] else '-'}")
            st.markdown(f"- **Umum:** {log[3] if log[3] else '-'}")
            st.divider()

        st.subheader("1. Buat Narasi Laporan")
        if st.button("⚡ Buat Rangkuman Evaluasi Otomatis", type="primary"):
          with st.spinner(
              "Sedang menyusun narasi evaluasi perkembangan siswa..."
          ):
            summary_res = generate_summary(s_nama, logs)
            st.session_state[f"summary_{selected_s_id}"] = summary_res
            st.success("Rangkuman narasi berhasil dibuat!")

        # Form pengeditan rangkuman
        summary_key = f"summary_{selected_s_id}"
        current_summary = st.session_state.get(summary_key, "")

        summary_text = st.text_area(
            "Hasil Rangkuman Evaluasi (Dapat diedit manual sebelum diunduh):",
            value=current_summary,
            height=250,
        )
        st.session_state[summary_key] = summary_text

        st.divider()
        st.subheader("2. Download Dokumen Word (.docx)")

        if summary_text.strip():
          docx_buffer = generate_docx(
              guru_data["nama_guru"],
              guru_data["nama_sekolah"],
              s_nama,
              s_nisn,
              summary_text,
              logs,
          )

          file_name_clean = (
              f"Laporan_Perkembangan_{s_nama.replace(' ', '_')}.docx"
          )

          st.download_button(
              label="📄 Download Laporan Word (.docx)",
              data=docx_buffer,
              file_name=file_name_clean,
              mime=(
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              ),
          )
        else:
          st.info(
              "💡 Klik tombol **'Buat Rangkuman Evaluasi Otomatis'** di atas"
              " terlebih dahulu untuk mengunduh berkas Word."
          )
