import streamlit as st
import openai

# Konfigurasi API (Ganti dengan API Key Anda)
openai.api_key = "YOUR_OPENAI_API_KEY"

def generate_laporan_ai(nama_siswa, catatan_guru):
    prompt = f"""
    Susunlah laporan capaian siswa bernama {nama_siswa} berdasarkan catatan guru berikut:
    "{catatan_guru}"
    
    Laporan harus mencakup deskripsi untuk 8 Dimensi ini:
    1. Keimanan & Ketakwaan
    2. Kewargaan
    3. Penalaran Kritis
    4. Kreativitas
    5. Kolaborasi
    6. Kemandirian
    7. Kesehatan
    8. Komunikasi
    
    Format: Gunakan bahasa Indonesia yang baku, profesional, dan suportif.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Anda adalah guru pakar penulisan rapor."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Antarmuka Aplikasi
st.title("AI Generator Laporan Wali Kelas")

nama_siswa = st.text_input("Nama Siswa")
catatan_mentah = st.text_area("Masukkan Catatan Singkat Guru (Contoh: Budi rajin ibadah, suka bagi bekal, kritis di kelas, tapi tulisan kurang rapi)")

if st.button("Generate Laporan Utuh"):
    if nama_siswa and catatan_mentah:
        with st.spinner('AI sedang menyusun laporan...'):
            laporan_final = generate_laporan_ai(nama_siswa, catatan_mentah)
            st.subheader(f"Hasil Laporan: {nama_siswa}")
            st.write(laporan_final)
            
            # Fitur Download
            st.download_button("Download Laporan (.txt)", laporan_final, file_name=f"Laporan_{nama_siswa}.txt")
    else:
        st.warning("Mohon isi nama dan catatan terlebih dahulu.")