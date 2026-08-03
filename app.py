import streamlit as st
import pandas as pd
import openai
from datetime import datetime
from docx import Document
from io import BytesIO
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTING API & KONEKSI ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNGSI LOGIN OTOMATIS (Simple & Friendly) ---
st.set_page_config(page_title="Jurnale - Sahabat Guru", layout="wide")

# Gunakan session_state agar login tidak hilang saat pindah menu
if 'user_key' not in st.session_state:
    st.session_state['user_key'] = ""

def login_page():
    st.title("Welcome to Jurnale 🎓")
    st.info("Aplikasi ini membantu Bapak/Ibu Guru menyusun narasi rapor dengan AI.")
    
    with st.container():
        st.subheader("Masuk ke Ruang Kerja Anda")
        # Guru cukup memasukkan nama atau email mereka (bebas)
        id_guru = st.text_input("Masukkan Nama Lengkap / Email (Tanpa Spasi):", placeholder="contoh: GuruAni / ani@sekolah.com")
        st.caption("Nama ini akan menjadi kunci folder data Anda. Pastikan selalu menggunakan nama yang sama.")
        
        if st.button("Masuk Sekarang"):
            if id_guru:
                st.session_state['user_key'] = id_guru.lower().strip()
                st.rerun()
            else:
                st.warning("Mohon isi nama/ID Anda.")

# Jika belum memasukkan ID, tampilkan halaman login
if not st.session_state['user_key']:
    login_page()
    st.stop()

# --- 3. JIKA SUDAH MASUK, AMBIL DATA ---
username = st.session_state['user_key']

# Tampilkan di Sidebar
st.sidebar.title(f"📍 Ruang Kerja: {username.upper()}")
if st.sidebar.button("Keluar / Ganti Akun"):
    st.session_state['user_key'] = ""
    st.rerun()

# --- 4. LOGIKA FILTER DATA (Kunci agar tidak tertukar) ---
def get_my_data(sheet_name):
    all_data = conn.read(worksheet=sheet_name)
    if all_data.empty:
        return all_data
    # Hanya ambil baris yang kolom 'Guru' nya sama dengan username yang login
    return all_data[all_data['Guru'] == username]

# Load data yang sudah difilter
df_siswa = get_my_data("siswa")
df_jurnal = get_my_data("jurnal")

# --- 5. MENU NAVIGASI ---
menu = st.sidebar.radio("Pilih Menu:", ["Biodata Siswa", "Isi Jurnal Harian", "Cetak Laporan AI"])

# --- BAGIAN SIMPAN DATA (Contoh untuk Biodata) ---
if menu == "Biodata Siswa":
    st.header("👥 Data Siswa Anda")
    with st.expander("Tambah Siswa"):
        nama_s = st.text_input("Nama Siswa")
        nisn_s = st.text_input("NISN")
        if st.button("Simpan Siswa"):
            # Ambil semua data asli untuk diupdate
            all_siswa = conn.read(worksheet="siswa")
            # Tambahkan data baru dengan kolom 'Guru'
            new_row = pd.DataFrame([{"Guru": username, "Nama": nama_s, "NISN": nisn_s}])
            updated_df = pd.concat([all_siswa, new_row], ignore_index=True)
            conn.update(worksheet="siswa", data=updated_df)
            st.success(f"Siswa {nama_s} berhasil disimpan di folder Anda!")
            st.rerun()
    
    st.dataframe(df_siswa[["Nama", "NISN"]], use_container_width=True)

# ... (Lanjutkan menu lainnya dengan logika yang sama: Selalu simpan kolom 'Guru')
