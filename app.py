import streamlit as st
import pandas as pd
import openai
from datetime import datetime
from docx import Document
from io import BytesIO
from streamlit_gsheets import GSheetsConnection # Perlu install: st-gsheets-connection

# --- 1. KONFIGURASI API ---
openai.api_key = st.secrets["OPENAI_API_KEY"] # Gunakan Secrets agar aman

# --- 2. KONEKSI GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_gsheet(sheet_name):
    return conn.read(worksheet=sheet_name)

# --- 3. FUNGSI LOGIN & SESSION ---
st.set_page_config(page_title="Wali Kelas Pro AI", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# Sidebar Login
with st.sidebar:
    st.title("🔐 Akses Guru")
    if not st.session_state['logged_in']:
        user_input = st.text_input("Nama Pengguna (Tanpa Spasi)")
        pass_input = st.text_input("Kata Sandi", type="password")
        if st.button("Masuk"):
            if user_input and pass_input == "guru123": # Ganti sandi ini
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_input.lower().strip()
                st.rerun()
    else:
        st.success(f"Halo, Guru {st.session_state['username']}")
        if st.button("Keluar"):
            st.session_state['logged_in'] = False
            st.rerun()

if not st.session_state['logged_in']:
    st.warning("Silakan login untuk mengakses data Anda.")
    st.stop()

# --- 4. AMBIL DATA & FILTER BERDASARKAN USER ---
# Ini rahasianya: Kita ambil semua data, tapi langsung kita filter hanya milik si user
username_aktif = st.session_state['username']

try:
    df_siswa_all = load_data_gsheet("siswa")
    df_siswa = df_siswa_all[df_siswa_all["Username_Guru"] == username_aktif]
    
    df_jurnal_all = load_data_gsheet("jurnal")
    df_jurnal = df_jurnal_all[df_jurnal_all["Username_Guru"] == username_aktif]
except:
    st.error("Gagal terhubung ke Google Sheets. Pastikan kolom sudah sesuai.")
    st.stop()

# --- 5. MENU NAVIGASI ---
menu = st.sidebar.radio("Navigasi:", ["Data Siswa", "Jurnal Harian", "Buat Laporan AI"])

if menu == "Data Siswa":
    st.header(f"👥 Manajemen Siswa - {username_aktif}")
    
    with st.form("tambah_siswa"):
        c1, c2 = st.columns(2)
        n_siswa = c1.text_input("Nama Siswa")
        n_nisn = c2.text_input("NISN")
        if st.form_submit_button("Simpan"):
            # Tambah ke Google Sheet
            new_data = pd.DataFrame([{"Username_Guru": username_aktif, "Nama_Siswa": n_siswa, "NISN": n_nisn}])
            updated_df = pd.concat([df_siswa_all, new_data], ignore_index=True)
            conn.update(worksheet="siswa", data=updated_df)
            st.success("Tersimpan!")
            st.rerun()

    st.dataframe(df_siswa, use_container_width=True)

elif menu == "Jurnal Harian":
    st.header(f"📝 Jurnal Harian - {username_aktif}")
    if df_siswa.empty:
        st.warning("Isi data siswa dulu.")
    else:
        with st.form("input_jurnal"):
            s_pilih = st.selectbox("Siswa", df_siswa["Nama_Siswa"])
            dimensi = st.selectbox("Dimensi", ["Keimanan", "Kewargaan", "Kritis", "Kreatif", "Kolaborasi", "Mandiri", "Kesehatan", "Komunikasi"])
            catatan = st.text_area("Hasil Observasi")
            if st.form_submit_button("Simpan Jurnal"):
                new_j = pd.DataFrame([{"Username_Guru": username_aktif, "Tanggal": datetime.now().date(), 
                                       "Nama_Siswa": s_pilih, "Dimensi": dimensi, "Catatan": catatan}])
                updated_jurnal = pd.concat([df_jurnal_all, new_j], ignore_index=True)
                conn.update(worksheet="jurnal", data=updated_jurnal)
                st.success("Jurnal berhasil disimpan!")
                st.rerun()
    
    st.subheader("Riwayat Jurnal Anda")
    st.table(df_jurnal)

elif menu == "Buat Laporan AI":
    st.header("🤖 Generator Laporan")
    if df_jurnal.empty:
        st.error("Belum ada data jurnal untuk diproses.")
    else:
        target = st.selectbox("Pilih Siswa", df_siswa["Nama_Siswa"])
        if st.button("Generate dengan AI"):
            # Ambil catatan hanya untuk siswa tersebut
            catatan_siswa = df_jurnal[df_jurnal["Nama_Siswa"] == target]["Catatan"].tolist()
            # ... (Panggil fungsi AI Anda seperti sebelumnya) ...
            st.info("AI sedang memproses... (Gunakan fungsi get_ai_response Anda di sini)")
