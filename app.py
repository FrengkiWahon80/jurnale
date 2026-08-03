import streamlit as st
from duckduckgo_search import DDGS

# Konfigurasi Halaman
st.set_page_config(page_title="AI Jurnale - Bebas API Key", page_icon="📝")

# Judul Aplikasi
st.title("📝 AI Jurnale (Versi Gratis)")
st.markdown("Aplikasi ini menggunakan akses AI gratis tanpa memerlukan API Key.")

# Fungsi untuk mendapatkan jawaban dari AI
def proses_ai(prompt_teks):
    try:
        with DDGS() as ddgs:
            # Menggunakan model gpt-4o-mini (Gratis & Cepat)
            # Pilihan model lain: 'llama-3-70b', 'mixtral-8x7b', 'claude-3-haiku'
            respon = ddgs.chat(prompt_teks, model='gpt-4o-mini')
            return respon
    except Exception as e:
        return f"Terjadi kesalahan teknis: {str(e)}"

# Form Input
with st.form("my_form"):
    user_input = st.text_area(
        "Masukkan teks, pertanyaan, atau draf jurnal Anda:",
        placeholder="Contoh: Buatkan ringkasan dari teks berikut...",
        height=200
    )
    
    submit_button = st.form_submit_button(label='Proses Sekarang')

# Logika ketika tombol ditekan
if submit_button:
    if user_input.strip() == "":
        st.warning("Mohon masukkan teks terlebih dahulu!")
    else:
        with st.spinner('Sedang memproses jawaban...'):
            hasil = proses_ai(user_input)
            
            st.subheader("Hasil Analisis AI:")
            st.markdown("---")
            st.write(hasil)
            st.markdown("---")
            
            # Tombol untuk download hasil sebagai teks
            st.download_button(
                label="Download Hasil (.txt)",
                data=hasil,
                file_name="hasil_jurnale.txt",
                mime="text/plain"
            )

# Footer
st.caption("Dibuat dengan Streamlit & DuckDuckGo AI (Tanpa API Key)")
