import streamlit as st
import pandas as pd
import openai
import os
from datetime import datetime

# --- KONFIGURASI API ---
# Ganti dengan API Key Anda atau set sebagai environment variable
openai.api_key = "MASUKKAN_API_KEY_OPENAI_ANDA"

# --- FUNGSI DATABASE SEDERHANA ---
def load_data(file_name, columns):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame(columns=columns)

def save_data(df, file_name):
    df.to_csv(file_name, index=False)

# --- FUNGSI AI ---
def generate_ai_report(nama, catatan_list):
    gabungan_catatan = " ".join(catatan_list)
    prompt = f"""
    Susunlah laporan akhir wali kelas untuk siswa bernama {nama}.
    Berdasarkan kumpulan catatan harian berikut: "{gabungan_catatan}"
    
    Buatlah deskripsi profesional untuk 8 Dimensi Kompetensi Lulusan:
    1. Keimanan, 2. Kewargaan, 3. Penalaran Kritis, 4. Kreativitas, 
    5. Kolaborasi, 6. Kemandirian, 7. Kesehatan, 8. Komunikasi.
    
    Gunakan bahasa Indonesia yang edukatif dan objektif.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Anda adalah guru wali kelas yang ahli menyusun deskripsi rapor."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Terjadi kesalahan pada AI: {e}"

# --- TAMPILAN APLIKASI ---
st.set_page_config(page_title="App Wali Kelas AI", layout="wide")
st.title("🏫 Sistem Informasi Wali Kelas & Jurnal AI")

# Menu Navigasi
menu = st.sidebar.selectbox("Pilih Menu", ["Data Siswa", "Isi Jurnal Harian", "Rekap & Generate Laporan AI"])

# Load Database
df_siswa = load_data("siswa.csv", ["Nama", "NISN"])
df_jurnal = load_data("jurnal.csv", ["Tanggal", "Nama", "Dimensi", "Catatan"])

# --- MENU 1: DATA SISWA ---
if menu == "Data Siswa":
    st.header("Manajemen Data Siswa")
    with st.form("tambah_siswa"):
        nama_baru = st.text_input("Nama Siswa Baru")
        nisn_baru = st.text_input("NISN")
        if st.form_submit_button("Tambah Siswa"):
            if nama_baru:
                new_row = pd.DataFrame({"Nama": [nama_baru], "NISN": [nisn_baru]})
                df_siswa = pd.concat([df_siswa, new_row], ignore_index=True)
                save_data(df_siswa, "siswa.csv")
                st.success("Siswa berhasil ditambahkan!")
                st.rerun()

    st.subheader("Daftar Murid Wali")
    st.table(df_siswa)

# --- MENU 2: ISI JURNAL HARIAN ---
elif menu == "Isi Jurnal Harian":
    st.header("Input Jurnal Harian Siswa")
    if df_siswa.empty:
        st.warning("Silakan isi data siswa terlebih dahulu di menu Data Siswa.")
    else:
        with st.form("form_jurnal"):
            nama_pilih = st.selectbox("Pilih Siswa", df_siswa["Nama"].tolist())
            dimensi_pilih = st.selectbox("Dimensi SKL", [
                "Keimanan", "Kewargaan", "Penalaran Kritis", "Kreativitas", 
                "Kolaborasi", "Kemandirian", "Kesehatan", "Komunikasi"
            ])
            catatan_guru = st.text_area("Apa yang terjadi hari ini?")
            tanggal = st.date_input("Tanggal Kejadian", datetime.now())
            
            if st.form_submit_button("Simpan ke Jurnal"):
                new_jurnal = pd.DataFrame({
                    "Tanggal": [tanggal],
                    "Nama": [nama_pilih],
                    "Dimensi": [dimensi_pilih],
                    "Catatan": [catatan_guru]
                })
                df_jurnal = pd.concat([df_jurnal, new_jurnal], ignore_index=True)
                save_data(df_jurnal, "jurnal.csv")
                st.success(f"Catatan untuk {nama_pilih} berhasil disimpan!")

    st.subheader("Riwayat Jurnal Terkini")
    st.dataframe(df_jurnal.tail(10))

# --- MENU 3: REKAP & AI GENERATOR ---
elif menu == "Rekap & Generate Laporan AI":
    st.header("Generate Laporan Otomatis (8 Dimensi)")
    if df_siswa.empty:
        st.warning("Belum ada data siswa.")
    else:
        siswa_target = st.selectbox("Pilih Siswa untuk Dibuatkan Laporan", df_siswa["Nama"].tolist())
        
        # Ambil semua catatan milik siswa tersebut
        catatan_siswa = df_jurnal[df_jurnal["Nama"] == siswa_target]
        
        if catatan_siswa.empty:
            st.info(f"Belum ada catatan jurnal untuk {siswa_target}. Silakan isi jurnal terlebih dahulu.")
        else:
            st.subheader(f"Ringkasan Aktivitas {siswa_target}")
            st.write(catatan_siswa[["Tanggal", "Dimensi", "Catatan"]])
            
            if st.button(f"Generate Laporan Narasi AI untuk {siswa_target}"):
                with st.spinner("AI sedang merangkum seluruh jurnal menjadi laporan 8 dimensi..."):
                    list_catatan = catatan_siswa["Catatan"].tolist()
                    hasil_ai = generate_ai_report(siswa_target, list_catatan)
                    st.markdown("---")
                    st.markdown("### HASIL LAPORAN AI")
                    st.write(hasil_ai)
                    
                    # Tombol Copy/Download
                    st.download_button("Download Laporan Teks", hasil_ai, file_name=f"Laporan_{siswa_target}.txt")
