import streamlit as st
import pandas as pd
import openai
import os
from datetime import datetime
from docx import Document
from io import BytesIO

# --- 1. KONFIGURASI API ---
# Masukkan API Key Anda di sini
openai.api_key = "MASUKKAN_API_KEY_ANDA_DI_SINI"

# --- 2. FUNGSI DATABASE (CSV) ---
def load_data(file_name, columns):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame(columns=columns)

def save_data(df, file_name):
    df.to_csv(file_name, index=False)

# --- 3. FUNGSI GENERATE WORD ---
def create_word_doc(nama_siswa, konten_ai, catatan_wali, nama_wali, nama_kepsek):
    doc = Document()
    doc.add_heading('LAPORAN CAPAIAN KOMPETENSI SISWA', 0)
    
    # Identitas Siswa
    p = doc.add_paragraph()
    p.add_run(f"Nama Siswa: ").bold = True
    p.add_run(nama_siswa)
    p.add_run(f"\nTanggal Cetak: {datetime.now().strftime('%d %B %Y')}")

    doc.add_heading('Hasil Observasi 8 Dimensi (Analisis AI):', level=1)
    doc.add_paragraph(konten_ai)
    
    doc.add_heading('Catatan Wali Kelas:', level=1)
    doc.add_paragraph(catatan_wali)

    doc.add_paragraph("\n\n")

    # Tabel Tanda Tangan
    table = doc.add_table(rows=4, cols=2)
    table.cell(0, 0).text = "Mengetahui,"
    table.cell(0, 1).text = f"Ditetapkan di: ___________"
    
    table.cell(1, 0).text = "Kepala Sekolah,"
    table.cell(1, 1).text = "Wali Kelas,"
    
    table.cell(2, 0).text = "\n\n" # Ruang tanda tangan
    table.cell(2, 1).text = "\n\n"
    
    table.cell(3, 0).text = f"( {nama_kepsek} )"
    table.cell(3, 1).text = f"( {nama_wali} )"

    target = BytesIO()
    doc.save(target)
    target.seek(0)
    return target

# --- 4. FUNGSI AI ---
def get_ai_response(nama, list_catatan):
    if not list_catatan:
        return "Belum ada data observasi untuk dianalisis."
    
    gabungan = " ".join(list_catatan)
    prompt = f"""
    Susunlah narasi laporan pendidikan untuk siswa bernama {nama}.
    Berdasarkan data observasi berikut: {gabungan}
    
    Wajib mencakup 8 dimensi ini dalam paragraf yang rapi:
    1. Keimanan, 2. Kewargaan, 3. Penalaran Kritis, 4. Kreativitas, 
    5. Kolaborasi, 6. Kemandirian, 7. Kesehatan, 8. Komunikasi.
    
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

# --- 5. TAMPILAN UTAMA ---
st.set_page_config(page_title="Wali Kelas Pro AI", layout="wide")

# Load Data
df_siswa = load_data("siswa.csv", ["Nama", "NISN"])
df_jurnal = load_data("jurnal.csv", ["Tanggal", "Nama", "Dimensi", "Catatan"])

st.sidebar.title("MENU UTAMA")
menu = st.sidebar.radio("Pilih Halaman:", ["Biodata Siswa", "Jurnal Harian", "Generate Laporan"])

# --- HALAMAN 1: BIODATA ---
if menu == "Biodata Siswa":
    st.header("👥 Manajemen Biodata Siswa")
    
    # Tambah Siswa
    with st.expander("➕ Tambah Siswa Baru"):
        with st.form("form_tambah"):
            nama_baru = st.text_input("Nama Lengkap")
            nisn_baru = st.text_input("NISN")
            submit = st.form_submit_button("Simpan Siswa")
            if submit and nama_baru:
                df_siswa = pd.concat([df_siswa, pd.DataFrame({"Nama":[nama_baru], "NISN":[nisn_baru]})], ignore_index=True)
                save_data(df_siswa, "siswa.csv")
                st.success("Data berhasil ditambah!")
                st.rerun()

    # Edit/Hapus dengan Data Editor
    st.subheader("Daftar Siswa (Edit langsung di tabel)")
    df_siswa_edited = st.data_editor(df_siswa, num_rows="dynamic", key="editor_siswa")
    if st.button("Simpan Perubahan Tabel"):
        save_data(df_siswa_edited, "siswa.csv")
        st.success("Database diperbarui!")
        st.rerun()

# --- HALAMAN 2: JURNAL ---
elif menu == "Jurnal Harian":
    st.header("📝 Jurnal Harian Siswa")
    if df_siswa.empty:
        st.warning("Silakan isi data siswa dulu di menu Biodata.")
    else:
        with st.form("form_jurnal"):
            nama_s = st.selectbox("Pilih Siswa", df_siswa["Nama"])
            dimensi = st.selectbox("Dimensi SKL", ["Keimanan", "Kewargaan", "Kritis", "Kreatif", "Kolaborasi", "Mandiri", "Kesehatan", "Komunikasi"])
            cat = st.text_area("Catatan Observasi Guru")
            tgl = st.date_input("Tanggal", datetime.now())
            if st.form_submit_button("Simpan Jurnal"):
                new_j = pd.DataFrame({"Tanggal":[tgl], "Nama":[nama_s], "Dimensi":[dimensi], "Catatan":[cat]})
                df_jurnal = pd.concat([df_jurnal, new_j], ignore_index=True)
                save_data(df_jurnal, "jurnal.csv")
                st.success("Catatan tersimpan!")

    st.subheader("Riwayat Jurnal")
    st.dataframe(df_jurnal, use_container_width=True)

# --- HALAMAN 3: REKAP & AI ---
elif menu == "Generate Laporan":
    st.header("🤖 AI Report Generator (8 Dimensi)")
    if df_siswa.empty:
        st.warning("Data siswa tidak ditemukan.")
    else:
        target_nama = st.selectbox("Pilih Siswa untuk Laporan", df_siswa["Nama"])
        
        col1, col2 = st.columns(2)
        nama_wali = col1.text_input("Nama Wali Kelas", "Nama Guru Anda, S.Pd")
        nama_kepsek = col2.text_input("Nama Kepala Sekolah", "Nama Kepsek, M.Pd")
        
        catatan_wali = st.text_area("Catatan/Pesan Khusus Wali Kelas", "Siswa menunjukkan prestasi yang stabil.")
        
        if st.button("Proses Laporan dengan AI"):
            data_jurnal = df_jurnal[df_jurnal["Nama"] == target_nama]["Catatan"].tolist()
            
            if not data_jurnal:
                st.error("Siswa ini belum memiliki catatan di Jurnal Harian.")
            else:
                with st.spinner("AI sedang merangkum 8 dimensi..."):
                    hasil_ai = get_ai_response(target_nama, data_jurnal)
                    st.markdown("### Preview Laporan")
                    st.info(hasil_ai)
                    
                    # Buat file Word
                    file_word = create_word_doc(target_nama, hasil_ai, catatan_wali, nama_wali, nama_kepsek)
                    
                    st.download_button(
                        label="📥 Download File Word (.docx)",
                        data=file_word,
                        file_name=f"Laporan_{target_nama}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
