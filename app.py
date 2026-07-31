import streamlit as st
import pandas as pd
import openai
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches
from io import BytesIO

# --- KONFIGURASI API ---
# Masukkan API Key OpenAI Anda di sini
openai.api_key = "MASUKKAN_API_KEY_ANDA_DI_SINI"

# --- FUNGSI DATABASE ---
def load_data(file_name, columns):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame(columns=columns)

def save_data(df, file_name):
    df.to_csv(file_name, index=False)

# --- FUNGSI WORD DENGAN TANDA TANGAN ---
def create_word_doc(nama_siswa, konten_laporan, catatan_wali, nama_wali, nama_kepsek):
    doc = Document()
    
    # Judul
    doc.add_heading('LAPORAN CAPAIAN KOMPETENSI SISWA', 0)
    
    # Identitas
    table_id = doc.add_table(rows=2, cols=2)
    table_id.cell(0, 0).text = "Nama Siswa:"
    table_id.cell(0, 1).text = nama_siswa
    table_id.cell(1, 0).text = "Tanggal Cetak:"
    table_id.cell(1, 1).text = datetime.now().strftime('%d %B %Y')

    doc.add_paragraph("\n" + "="*50 + "\n")
    
    # Isi Laporan dari AI
    doc.add_heading('Hasil Observasi 8 Dimensi:', level=1)
    doc.add_paragraph(konten_laporan)
    
    doc.add_paragraph("\n" + "-"*50)
    
    # Catatan Tambahan Wali Kelas
    doc.add_heading('Catatan Wali Kelas:', level=2)
    doc.add_paragraph(catatan_wali)

    doc.add_paragraph("\n\n")

    # Tanda Tangan (Tabel agar rapi kiri-kanan)
    table_sig = doc.add_table(rows=4, cols=2)
    table_sig.cell(0, 0).text = "Mengetahui,"
    table_sig.cell(0, 1).text = "Kota, " + datetime.now().strftime('%d %B %Y')
    
    table_sig.cell(1, 0).text = "Kepala Sekolah,"
    table_sig.cell(1, 1).text = "Wali Kelas,"
    
    # Spasi Tanda Tangan
    table_sig.cell(2, 0).text = "\n\n"
    table_sig.cell(2, 1).text = "\n\n"
    
    table_sig.cell(3, 0).text = f"( {nama_kepsek} )"
    table_sig.cell(3, 1).text = f"( {nama_wali} )"

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- FUNGSI AI ---
def generate_ai_report(nama, catatan_list):
    gabungan = " ".join(catatan_list)
    prompt = f"Susun laporan 8 dimensi SKL (Keimanan, Kewargaan, Kritis, Kreatif, Kolaborasi, Mandiri, Sehat, Komunikasi) untuk {nama} berdasarkan data: {gabungan}. Gunakan narasi profesional."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Anda guru profesional."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "Gagal generate laporan AI. Periksa API Key."

# --- INITIAL LOAD DATA ---
df_siswa = load_data("siswa.csv", ["Nama", "NISN"])
df_jurnal = load_data("jurnal.csv", ["Tanggal", "Nama", "Dimensi", "Catatan"])

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("Navigasi")
menu = st.sidebar.selectbox("Pilih Menu", ["Data Siswa", "Isi Jurnal Harian", "Rekap & Generate AI"])

# --- LOGIKA HALAMAN ---

if menu == "Data Siswa":
    st.header("👥 Manajemen Data Siswa")
    
    # Tambah Siswa
    with st.expander("➕ Tambah Siswa"):
        with st.form("tambah"):
            n = st.text_input("Nama Siswa")
            ni = st.text_input("NISN")
            if st.form_submit_button("Simpan"):
                df_siswa = pd.concat([df_siswa, pd.DataFrame({"Nama":[n], "NISN":[ni]})], ignore_index=True)
                save_data(df_siswa, "siswa.csv")
                st.success("Tersimpan!")
                st.rerun()

    # Edit & Hapus
    st.subheader("Daftar Siswa")
    edited_df = st.data_editor(df_siswa, num_rows="dynamic")
    if st.button("Simpan Perubahan"):
        save_data(edited_df, "siswa.csv")
        st.success("Data diperbarui!")
        st.rerun()

elif menu == "Isi Jurnal Harian":
    st.header("📝 Jurnal Harian")
    if df_siswa.empty:
        st.warning("Isi data siswa dulu.")
    else:
        with st.form("jurnal"):
            nama = st.selectbox("Siswa", df_siswa["Nama"])
            dim = st.selectbox("Dimensi", ["Keimanan", "Kewargaan", "Kritis", "Kreatif", "Kolaborasi", "Mandiri", "Kesehatan", "Komunikasi"])
            txt = st.text_area("Catatan Kejadian")
            if st.form_submit_button("Simp
