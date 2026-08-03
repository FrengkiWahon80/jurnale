import streamlit as st
import pandas as pd
import openai
import os
from datetime import datetime
from docx import Document
from io import BytesIO

# --- 1. KONFIGURASI API ---
openai.api_key = "MASUKKAN_API_KEY_ANDA_DI_SINI"

# --- 2. FUNGSI DATABASE (DIPERBAIKI: Menggunakan Nama File Unik per User) ---
def load_data(username, tipe_data, columns):
    # Nama file unik: misal 'budi_siswa.csv' atau 'ani_jurnal.csv'
    file_name = f"data_{username}_{tipe_data}.csv"
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame(columns=columns)

def save_data(df, username, tipe_data):
    file_name = f"data_{username}_{tipe_data}.csv"
    df.to_csv(file_name, index=False)

# --- 3. FUNGSI GENERATE WORD (Tetap sama) ---
def create_word_doc(nama_siswa, konten_ai, catatan_wali, nama_wali, nama_kepsek):
    doc = Document()
    doc.add_heading('LAPORAN CAPAIAN KOMPETENSI SISWA', 0)
    p = doc.add_paragraph()
    p.add_run(f"Nama Siswa: ").bold = True
    p.add_run(nama_siswa)
    p.add_run(f"\nTanggal Cetak: {datetime.now().strftime('%d %B %Y')}")
    doc.add_heading('Hasil Observasi 8 Dimensi (Analisis AI):', level=1)
    doc.add_paragraph(konten_ai)
    doc.add_heading('Catatan Wali Kelas:', level=1)
    doc.add_paragraph(catatan_wali)
    doc.add_paragraph("\n\n")
    table = doc.add_table(rows=4, cols=2)
    table.cell(0, 0).text = "Mengetahui,"
    table.cell(0, 1).text = f"Ditetapkan di: ___________"
    table.cell(1, 0).text = "Kepala Sekolah,"
    table.cell(1, 1).text = "Wali Kelas,"
    table.cell(3, 0).text = f"( {nama_kepsek} )"
    table.cell(3, 1).text = f"( {nama_wali} )"
    target = BytesIO()
    doc.save(target)
    target.seek(0)
    return target

# --- 4. FUNGSI AI (Tetap sama) ---
def get_ai_response(nama, list_catatan):
    if not list_catatan:
        return "Belum ada data observasi untuk dianalisis."
    gabungan = " ".join(list_catatan)
    prompt = f"""
    Susunlah narasi laporan pendidikan untuk siswa bernama {nama}.
    Berdasarkan data observasi berikut: {gabungan}
    Wajib mencakup 8 dimensi ini: 1. Keimanan, 2. Kewargaan, 3. Penalaran Kritis, 
    4. Kreativitas, 5. Kolaborasi, 6. Kemandirian, 7. Kesehatan, 8. Komunikasi.
    Gunakan bahasa Indonesia yang formal dan memotivasi.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Anda adalah guru pakar penulisan rapor."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error AI: {str(e)}"

# --- 5. SISTEM LOGIN SEDERHANA ---
st.set_page_config(page_title="Wali Kelas Pro AI", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

def login():
    st.sidebar.title("🔐 Login Guru")
    user = st.sidebar.text_input("Username (Tanpa spasi)")
    pw = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Masuk"):
        if user and pw == "guru123": # Ganti password sesuai keinginan
            st.session_state['logged_in'] = True
            st.session_state['username'] = user.lower().strip()
            st.rerun()
        else:
            st.sidebar.error("Username/Password salah")

if not st.session_state['logged_in']:
    login()
    st.info("Silakan login di sidebar untuk mengelola data jurnal Anda.")
    st.stop() # Menghentikan aplikasi jika belum login

# --- 6. TAMPILAN UTAMA (Setelah Login) ---
username = st.session_state['username']
st.sidebar.success(f"Login sebagai: {username}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# Load Data Spesisik User
df_siswa = load_data(username, "siswa", ["Nama", "NISN"])
df_jurnal = load_data(username, "jurnal", ["Tanggal", "Nama", "Dimensi", "Catatan"])

st.sidebar.title("MENU UTAMA")
menu = st.sidebar.radio("Pilih Halaman:", ["Biodata Siswa", "Jurnal Harian", "Generate Laporan"])

# --- HALAMAN 1: BIODATA ---
if menu == "Biodata Siswa":
    st.header(f"👥 Biodata Siswa - Guru: {username}")
    with st.expander("➕ Tambah Siswa Baru"):
        with st.form("form_tambah"):
            nama_baru = st.text_input("Nama Lengkap")
            nisn_baru = st.text_input("NISN")
            submit = st.form_submit_button("Simpan Siswa")
            if submit and nama_baru:
                new_row = pd.DataFrame({"Nama":[nama_baru], "NISN":[nisn_baru]})
                df_siswa = pd.concat([df_siswa, new_row], ignore_index=True)
                save_data(df_siswa, username, "siswa")
                st.success("Data berhasil ditambah!")
                st.rerun()

    st.subheader("Daftar Siswa")
    df_siswa_edited = st.data_editor(df_siswa, num_rows="dynamic")
    if st.button("Simpan Perubahan Tabel"):
        save_data(df_siswa_edited, username, "siswa")
        st.success("Database diperbarui!")

# --- HALAMAN 2: JURNAL ---
elif menu == "Jurnal Harian":
    st.header(f"📝 Jurnal Harian - Guru: {username}")
    if df_siswa.empty:
        st.warning("Data siswa kosong. Isi biodata dulu.")
    else:
        with st.form("form_jurnal"):
            nama_s = st.selectbox("Pilih Siswa", df_siswa["Nama"])
            dimensi = st.selectbox("Dimensi SKL", ["Keimanan", "Kewargaan", "Kritis", "Kreatif", "Kolaborasi", "Mandiri", "Kesehatan", "Komunikasi"])
            cat = st.text_area("Catatan Observasi Guru")
            tgl = st.date_input("Tanggal", datetime.now())
            if st.form_submit_button("Simpan Jurnal"):
                new_j = pd.DataFrame({"Tanggal":[tgl], "Nama":[nama_s], "Dimensi":[dimensi], "Catatan":[cat]})
                df_jurnal = pd.concat([df_jurnal, new_j], ignore_index=True)
                save_data(df_jurnal, username, "jurnal")
                st.success("Catatan tersimpan!")
    
    st.subheader("Riwayat Jurnal Anda")
    st.dataframe(df_jurnal, use_container_width=True)

# --- HALAMAN 3: REKAP & AI ---
elif menu == "Generate Laporan":
    st.header("🤖 AI Report Generator")
    if df_siswa.empty:
        st.warning("Data siswa tidak ditemukan.")
    else:
        target_nama = st.selectbox("Pilih Siswa", df_siswa["Nama"])
        col1, col2 = st.columns(2)
        nama_wali = col1.text_input("Nama Wali Kelas", f"Guru {username}")
        nama_kepsek = col2.text_input("Nama Kepala Sekolah", "Nama Kepsek, M.Pd")
        catatan_wali = st.text_area("Catatan Wali Kelas", "Siswa menunjukkan perkembangan positif.")
        
        if st.button("Proses Laporan"):
            # Filter jurnal hanya milik siswa ini (yang sudah terfilter per guru)
            data_jurnal = df_jurnal[df_jurnal["Nama"] == target_nama]["Catatan"].tolist()
            
            if not data_jurnal:
                st.error("Belum ada catatan jurnal untuk siswa ini.")
            else:
                with st.spinner("AI sedang bekerja..."):
                    hasil_ai = get_ai_response(target_nama, data_jurnal)
                    st.info(hasil_ai)
                    file_word = create_word_doc(target_nama, hasil_ai, catatan_wali, nama_wali, nama_kepsek)
                    st.download_button(label="📥 Download Word", data=file_word, file_name=f"Laporan_{target_nama}.docx")
